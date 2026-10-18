"""Uncalibrated averaged buck reference and an independently fitted surrogate.

All energies are joules, times seconds, powers watts. This is a virtual circuit,
not a device-specific STM32 or regulator model. See ENERGY_MODEL.md.
"""

from dataclasses import dataclass
import math

import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class Segment:
    duration_s: float
    power_w: float


@dataclass(frozen=True)
class Buck:
    vin_v: float = 5.0
    vout_v: float = 3.3
    inductance_h: float = 22e-6
    capacitance_f: float = 10e-6
    resistance_ohm: float = 0.3
    iq_a: float = 2e-6
    inner_tau_s: float = 10e-6
    voltage_kp_a_per_v: float = 0.2
    voltage_ki_a_per_vs: float = 2000.0


@dataclass(frozen=True)
class CircuitResult:
    source_j: float
    raw_source_j: float
    load_j: float
    conduction_j: float
    quiescent_j: float
    storage_delta_j: float
    balance_error_j: float
    min_voltage_v: float
    max_voltage_v: float
    warmup_periods: int


@dataclass(frozen=True)
class HistoryFit:
    tau_s: float
    coefficient_ohm: float
    training_rmse_j: float
    calibration_cases: int


def validate(trace, supply):
    values = vars(supply)
    if not all(math.isfinite(v) for v in values.values()):
        raise ValueError("Supply parameters must be finite")
    if not (supply.vin_v > supply.vout_v > 0):
        raise ValueError("Buck requires vin > nominal vout > 0")
    for key in ("inductance_h", "capacitance_f", "inner_tau_s",
                "voltage_kp_a_per_v", "voltage_ki_a_per_vs"):
        if values[key] <= 0:
            raise ValueError(f"{key} must be positive")
    if supply.resistance_ohm < 0 or supply.iq_a < 0:
        raise ValueError("Loss and quiescent-current parameters cannot be negative")
    if not trace or any(not math.isfinite(s.duration_s) or not math.isfinite(s.power_w)
                        or s.duration_s <= 0 or s.power_w < 0 for s in trace):
        raise ValueError("Trace needs positive durations and finite nonnegative powers")
    if not math.isfinite(sum(s.duration_s for s in trace)):
        raise ValueError("Trace duration overflow")
    # Restrict comparisons to loads with an attainable regulated equilibrium.
    # Otherwise the nominal-voltage baseline has static saturation error even
    # for constant demand, which cannot be attributed to additional history.
    if any(supply.vout_v + supply.resistance_ohm * s.power_w / supply.vout_v >=
           supply.vin_v for s in trace):
        raise ValueError("Load has no available nominal operating point (duty must be < 1)")


def steady_energy(trace, supply):
    """Strong operating-point baseline, applied to every demand segment."""
    validate(trace, supply)
    return sum(s.duration_s * (s.power_w + supply.resistance_ohm *
                              (s.power_w / supply.vout_v) ** 2 +
                              supply.vin_v * supply.iq_a) for s in trace)


def circuit_energy(trace, supply, rtol=1e-8):
    """Solve a periodic, bidirectional averaged synchronous buck circuit.

    The ideal current controller requests a duty ratio; the power stage still
    obeys L di/dt = Vin*d - v - R*i and C dv/dt = i - P/v. Duty is bounded.
    Source power is Vin*d*i + Vin*Iq. The source can absorb returned energy.
    Warm-up is excluded, and remaining storage change is explicitly corrected.
    """
    validate(trace, supply)
    if not math.isfinite(rtol) or not 0 < rtol < 0.01:
        raise ValueError("rtol must be finite and between zero and 0.01")
    vref, vin = supply.vout_v, supply.vin_v
    peak_i = max(max(s.power_w for s in trace) / vref, 1e-3)
    first_i = trace[0].power_w / vref
    state = np.array([first_i, vref, first_i], dtype=float)

    def period(initial):
        y = np.array([*initial, 0.0, 0.0])
        minimum = maximum = float(initial[1])
        for segment in trace:
            def derivative(_time, x):
                current, voltage, integral = x[:3]
                if voltage <= 0.1 * vref or not np.all(np.isfinite(x)):
                    raise ValueError("Virtual rail collapsed or state is nonfinite")
                error = vref - voltage
                reference_i = supply.voltage_kp_a_per_v * error + integral
                requested = (voltage + supply.resistance_ohm * current +
                             supply.inductance_h * (reference_i - current) /
                             supply.inner_tau_s) / vin
                duty = min(1.0, max(0.0, requested))
                integral_rate = supply.voltage_ki_a_per_vs * error
                if (requested >= 1 and error > 0) or (requested <= 0 and error < 0):
                    integral_rate = 0.0
                return [(vin * duty - voltage - supply.resistance_ohm * current) /
                        supply.inductance_h,
                        (current - segment.power_w / voltage) / supply.capacitance_f,
                        integral_rate,
                        vin * duty * current + vin * supply.iq_a,
                        supply.resistance_ohm * current * current]

            solved = solve_ivp(derivative, (0, segment.duration_s), y, method="Radau",
                               rtol=rtol, atol=[1e-11, 1e-10, 1e-11, 1e-16, 1e-16])
            if not solved.success:
                raise ValueError("Circuit integration failed: " + solved.message)
            minimum = min(minimum, float(np.min(solved.y[1])))
            maximum = max(maximum, float(np.max(solved.y[1])))
            if minimum < 0.8 * vref or maximum > 1.2 * vref:
                raise ValueError("Virtual rail exceeded the model's +/-20% validity bound")
            y = solved.y[:, -1]
        return y, minimum, maximum

    scales = np.array([peak_i, vref, peak_i])
    for warmup in range(1, 101):
        end, _, _ = period(state)
        error = float(np.max(np.abs(end[:3] - state) / scales))
        state = end[:3]
        if error < 1e-8:
            break
    else:
        raise ValueError("Periodic circuit state did not converge in 100 periods")
    end, minimum, maximum = period(state)
    storage = (0.5 * supply.inductance_h * (end[0] ** 2 - state[0] ** 2) +
               0.5 * supply.capacitance_f * (end[1] ** 2 - state[1] ** 2))
    load = sum(s.power_w * s.duration_s for s in trace)
    quiescent = vin * supply.iq_a * sum(s.duration_s for s in trace)
    raw, conduction = float(end[3]), float(end[4])
    balance = raw - load - conduction - quiescent - storage
    if abs(balance) > max(1e-12, 1e-6 * max(load, raw)):
        raise ValueError("Reference circuit failed energy conservation")
    return CircuitResult(raw - storage, raw, load, conduction, quiescent, storage,
                         balance, minimum, maximum, warmup)


def history_feature(trace, tau_s, voltage_v):
    """Exact periodic integral of (I_demand - filtered_I)**2, in A²s."""
    if not math.isfinite(tau_s) or tau_s <= 0 or not math.isfinite(voltage_v) or voltage_v <= 0:
        raise ValueError("History time constant and voltage must be finite and positive")
    validate(trace, Buck(vin_v=voltage_v * 2, vout_v=voltage_v))
    currents = [s.power_w / voltage_v for s in trace]
    if max(currents) == min(currents):
        return 0.0
    value = 0.0
    for segment, current in zip(trace, currents):
        decay = math.exp(-segment.duration_s / tau_s)
        value = decay * value + (-math.expm1(-segment.duration_s / tau_s)) * current
    value /= -math.expm1(-sum(s.duration_s for s in trace) / tau_s)
    total = 0.0
    for segment, current in zip(trace, currents):
        total += (current - value) ** 2 * (tau_s / 2) * (-math.expm1(-2 * segment.duration_s / tau_s))
        value = current + (value - current) * math.exp(-segment.duration_s / tau_s)
    return total


def fit_history(training, supply, tau_candidates):
    """Fit on calibration pulse experiments only, never the scored FIR cases."""
    if not training or not tau_candidates:
        raise ValueError("Calibration traces and time-constant candidates are required")
    residuals = [circuit_energy(trace, supply).source_j - steady_energy(trace, supply)
                 for trace in training]
    best = None
    for tau in tau_candidates:
        features = [history_feature(trace, tau, supply.vout_v) for trace in training]
        denominator = sum(value * value for value in features)
        coefficient = sum(f * r for f, r in zip(features, residuals)) / denominator if denominator else 0
        # Do not let the correction imply negative total conduction loss.
        # A periodic first-order high-pass feature has L2 gain <= 1.
        coefficient = max(-supply.resistance_ohm, coefficient)
        rmse = math.sqrt(sum((r - coefficient * f) ** 2 for r, f in zip(residuals, features)) /
                         len(training))
        fitted = HistoryFit(tau, coefficient, rmse, len(training))
        if best is None or rmse < best.training_rmse_j:
            best = fitted
    return best


def history_energy(trace, supply, fitted):
    result = steady_energy(trace, supply) + fitted.coefficient_ohm * history_feature(
        trace, fitted.tau_s, supply.vout_v)
    if not math.isfinite(result) or result < 0:
        raise ValueError("History predictor produced invalid energy")
    return result
