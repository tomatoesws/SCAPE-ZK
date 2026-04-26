# Off-chain/System Primitive Equations

All baseline curves are reconstructed from `baselines/offchain_system_primitive_equations.csv`.
All primitive timings are loaded from local benchmark CSVs.

## Primitive Values

- `Tecc_verify` = `0.070838701` ms
- `Texp_G1` = `0.776954453` ms
- `Texp_GT` = `0.084769457` ms
- `Tgrp` = `0.456854000` ms
- `Thash32` = `0.002215000` ms
- `Thash_1KB` = `0.000836733` ms
- `Tpair` = `14.724512000` ms
- `Tsym_dec_1KB` = `0.000873799` ms
- `Tsym_enc_1KB` = `0.005631000` ms

## Baseline Equations

- Graph `authorization_preparation`, `XAuth [6]`: `r*(2*Tpair + 4*Texp_G1 + 2*Tgrp + 3*Thash32)`
- Graph `authorization_preparation`, `SSL-XIoMT [8]`: `r*(Tpair + 3*Texp_G1 + Tgrp + 2*Thash32)`
- Graph `authorization_preparation`, `Scheme [26]`: `r*(2*Tpair + 4*Texp_G1 + Tgrp + Thash32)`
- Graph `cross_domain_delegation`, `Traditional Re-encryption`: `mb*1024*(Tsym_dec_1KB + Tsym_enc_1KB)`
