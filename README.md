# Dalton Lab – Microneedle Array Passivation

Automation for coating solid microneedle arrays with SU-8 photopolymer, leaving only the tips exposed. This work was done at the Dalton Lab, University of Calgary.

| Folder | What it is |
|---|---|
| [`v2-marlin/`](v2-marlin/) | **Current system (Summer 2026).** SKR V1.3 + Marlin with a custom `M800` solenoid pulse, pneumatic dispensing, automated developer dip / IPA rinse, SEM validation data |
| [`v1-syringe-pump/`](v1-syringe-pump/) | Original design this was built from. Arduino Mega + CNC shield, syringe pump, SOPs, BOM, and the technical design report |

## Summer 2026 result

The automated process gave tip heights comparable to the manual method, measured by SEM with n = 8 needles × 3 arrays per process:

| Process | Mean tip height | S.D. |
|---|---|---|
| Automated | ~242.5 µm | ~3.3 µm |
| Manual | ~249.0 µm | ~3.7 µm |

The spread is similar for both processes, and at this sample size the two can't be told apart. Most of the remaining variability is attributed to the planarity of the vacuum chuck.
