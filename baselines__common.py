from dataclasses import dataclass

@dataclass(frozen=True)

class Sizes:

    G1: int = 48

    G2: int = 96

    GT: int = 576

    Zp: int = 32

    H:  int = 32

SIZES_BLS12381 = Sizes()

SIZES_TYPEF = Sizes(G1=128, G2=128, GT=128, Zp=20, H=32)

@dataclass(frozen=True)

class OpTimes:


    T_pair: float

    T_sm:   float

    T_exp:  float

    T_h:    float

    T_mul:  float

OPS_TYPEF_I7 = OpTimes(

    T_pair=4.20,

    T_sm=2.30,

    T_exp=1.80,

    T_h=0.01,

    T_mul=0.02,

)

OPS_BLS12381_I7 = OpTimes(

    T_pair=1.80,

    T_sm=0.28,

    T_exp=0.45,

    T_h=0.02,

    T_mul=0.005,

)

def scale_to(from_ops: OpTimes, ghz_from: float, ghz_to: float) -> OpTimes:


    r = ghz_from / ghz_to

    return OpTimes(

        T_pair=from_ops.T_pair * r,

        T_sm=from_ops.T_sm   * r,

        T_exp=from_ops.T_exp * r,

        T_h=from_ops.T_h    * r,

        T_mul=from_ops.T_mul * r,

    )
