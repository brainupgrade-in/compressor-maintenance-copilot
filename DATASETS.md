# Datasets for the Intelligent Industry track (checked 4 Oct 2026)

Rule: the repo is public and MIT-licensed, so **never commit raw data**. Ship a download script
and cite the source. Prefer the original UCI copy where the Kaggle mirror has a worse licence.

## Machine-level data (Kaggle / UCI)

| Dataset | What it is | Licence | Use |
|---|---|---|---|
| **MetroPT-3** (UCI 791; Kaggle `joebeachcapital/metropt-3-dataset`) | Real air compressor on a Porto metro train, Feb–Aug 2020, 1.5 M rows, 15 sensors (pressures, motor current, oil temp, valves) | CC BY 4.0 | **Primary.** Real data with 4 dated air-leak failures and maintenance dates, so we can show how early the system would have warned. |
| **AI4I 2020** (UCI 601) | Synthetic milling machine, 10k rows, 5 labelled failure modes (tool wear, heat, power, overstrain, random) | CC BY 4.0 on UCI (Kaggle mirror says CC BY-NC-SA, use UCI) | Second machine with named failure modes for the explanation layer. |
| NASA IMS bearing (Kaggle `vinayak123tyagi/bearing-dataset`) | Run-to-failure vibration of 4 bearings, 1.6 GB | U.S. Government work | Optional third asset; large download. |
| Hydraulic test rig (UCI 447; Kaggle `jjacostupa/...`) | Multi-sensor condition monitoring of cooler, valve, pump, accumulator | CC BY 4.0 on UCI (Kaggle copy "unknown") | Alternative to AI4I. |
| Casting defect images (Kaggle `ravirajsinh45/...`) | Submersible pump impeller images, OK/defective | CC BY-NC-ND 4.0 | Only if we add visual inspection; download at run time, never redistribute. |
| Pump sensor data (Kaggle `nphantawee/pump-sensor-data`) | 52 sensors, 7 failures | unknown | Avoid: no licence. |

MetroPT-3 failure log (from UCI): 18 Apr air leak (high stress) · 29–30 May air leak · 5–7 Jun air leak
· 15 Jul air leak, with maintenance on 30 Apr, 8 Jun and 16 Jul.

Citation: Davari, Veloso, Ribeiro, Gama (2021). MetroPT-3 Dataset. UCI ML Repository. doi:10.24432/C5VW3R

## data.gov.in (India open data)

No machine-level or sensor data. Its search returns national aggregates. Useful only for the
**business-value slides**:
- Factory accident and injury statistics (DGFASLI, NCRB "factory/machine accidents"); also mirrored
  on dataful.in.
- "List of MSME Registered Units under UDYAM" (Ministry of MSME) for sizing the market of small manufacturers.
