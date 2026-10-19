"""Fetch exact public dependencies for the CMSIS-DSP baseline."""
import hashlib
import urllib.request

from simulator import BUILD, command

PIN="3a04f817a4380c00ff51f9bcdc6c4e4bb7a18b80"
HEADERS={
    "cmsis_version.h":"184c19fd3ee73632edf35a0b4d49cd48be75fbf49e6ccb19d9db05fa83bea4b3",
    "cmsis_gcc.h":"43bfd1fe69fbbc2ca70aaf7d43cc3e20f16e0c7f66e1bdef9b51af6dc14b2617",
    "cmsis_compiler.h":"b51963d271c1571ca3463654c76aa7ea50c4eac5d0a2710df10414ac64d9e0f8",
}


def main():
    BUILD.mkdir(exist_ok=True)
    dsp=BUILD/"cmsis-dsp"
    if not dsp.exists():
        command(["git","clone","--depth","1","--filter=blob:none","--sparse",
                 "--branch","v1.14.4","https://github.com/ARM-software/CMSIS-DSP.git",dsp])
    assert command(["git","rev-parse","HEAD"],dsp).stdout.strip()==PIN
    if not (dsp/"Source/FilteringFunctions/arm_fir_q15.c").exists():
        command(["git","sparse-checkout","set","Include","Source/FilteringFunctions"],dsp)
    assert not command(["git","status","--porcelain"],dsp).stdout.strip()
    core=BUILD/"cmsis-core"
    core.mkdir(exist_ok=True)
    for name,expected in HEADERS.items():
        path=core/name
        if not path.exists():
            url="https://raw.githubusercontent.com/ARM-software/CMSIS_5/5.9.0/CMSIS/Core/Include/"+name
            with urllib.request.urlopen(url,timeout=20) as response:
                data=response.read()
            assert hashlib.sha256(data).hexdigest()==expected,name
            path.write_bytes(data)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,name
    print("Verified CMSIS-DSP commit and the three pinned Core-header checksums.")


if __name__=="__main__":
    main()
