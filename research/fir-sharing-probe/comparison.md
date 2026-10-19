# Complete primary comparison

Descriptive; negative overhead means the best tested transposed kernel costs less modeled CPU energy than the strongest tested nontransposed control. These are 24 repeated experimental groups for three filter designs, not 24 independent applications.

| Compiler | Filter | Magnitude guarantee | Block | Best transposed | Best nontransposed | Transposed overhead |
|---|---|---:|---:|---|---|---:|
| gcc10 | speech_lp48 | 1024 | 1 | trans_hcub_demand | spec_fold | +3.42% |
| gcc10 | speech_lp48 | 1024 | 64 | trans_hcub_demand | spec_fold | +22.86% |
| gcc10 | speech_lp48 | 32768 | 1 | trans_hcub_demand | spec_fold | +3.42% |
| gcc10 | speech_lp48 | 32768 | 64 | trans_hcub_demand | spec_fold | +22.86% |
| gcc10 | speech_minphase48 | 1024 | 1 | trans_const | spec_direct | -1.13% |
| gcc10 | speech_minphase48 | 1024 | 64 | trans_hcub_demand | spec_direct | +13.08% |
| gcc10 | speech_minphase48 | 32768 | 1 | trans_const | cmsis64_unroll | -31.97% |
| gcc10 | speech_minphase48 | 32768 | 64 | trans_hcub_demand | cmsis64_unroll | -33.26% |
| gcc10 | vibration_bp192 | 1024 | 1 | trans_hcub_demand | spec_fold | +3.52% |
| gcc10 | vibration_bp192 | 1024 | 64 | trans_hcub_demand | spec_fold | +9.55% |
| gcc10 | vibration_bp192 | 32768 | 1 | trans_const | fold64 | +78.29% |
| gcc10 | vibration_bp192 | 32768 | 64 | trans_hcub_demand | spec_fold | +41.95% |
| gcc15 | speech_lp48 | 1024 | 1 | trans_hcub_demand | fold32 | -16.81% |
| gcc15 | speech_lp48 | 1024 | 64 | trans_hcub_demand | spec_fold | -3.03% |
| gcc15 | speech_lp48 | 32768 | 1 | trans_hcub_demand | fold32 | -16.81% |
| gcc15 | speech_lp48 | 32768 | 64 | trans_hcub_demand | spec_fold | -3.03% |
| gcc15 | speech_minphase48 | 1024 | 1 | trans_hcub_demand | cmsis32_unroll | -6.69% |
| gcc15 | speech_minphase48 | 1024 | 64 | trans_hcub_demand | cmsis32_unroll | +5.52% |
| gcc15 | speech_minphase48 | 32768 | 1 | trans_hcub_demand | cmsis64_unroll | -33.78% |
| gcc15 | speech_minphase48 | 32768 | 64 | trans_hcub_demand | cmsis64_unroll | -32.94% |
| gcc15 | vibration_bp192 | 1024 | 1 | trans_hcub_demand | fold32 | -5.93% |
| gcc15 | vibration_bp192 | 1024 | 64 | trans_hcub_demand | spec_fold | -8.69% |
| gcc15 | vibration_bp192 | 32768 | 1 | trans_hcub_demand | fold64 | +54.99% |
| gcc15 | vibration_bp192 | 32768 | 64 | trans_hcub_demand | fold64 | +19.29% |
