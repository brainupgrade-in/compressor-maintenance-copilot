# APU-300 Air Production Unit — Operating and Troubleshooting Manual (SYNTHETIC)

> Synthetic document written for the Compressor Maintenance Copilot demo. Not a real product manual.

## 1. System overview
The APU produces compressed air for pneumatic consumers (brakes, actuators, tools). An electric motor
drives an oil-injected screw compressor. Air passes an air-oil separator, a twin-tower desiccant dryer
and a check valve into the main reservoirs. The compressor runs in **load/unload cycles**: it loads when
reservoir pressure falls to the cut-in point (about 8.2 bar) and unloads at cut-out (about 10.0 bar).

## 2. Sensors and signals
| Tag | Meaning | Normal behaviour |
|---|---|---|
| TP2 | Compressor outlet pressure (bar) | ~9 bar while loading, near 0 when unloaded |
| TP3 | Pneumatic panel pressure (bar) | follows reservoir, 8.2–10.0 bar |
| H1 | Pressure after the separator / cyclonic filter | close to TP3; drop above 0.5 bar means restriction |
| DV_pressure | Pressure drop when the dryer towers discharge water | spikes briefly at tower changeover only |
| Reservoirs | Main reservoir pressure (bar) | 8.2–10.0 bar sawtooth |
| Oil_temperature | Compressor oil temperature (°C) | 55–75 °C running; alarm at 95 °C |
| Motor_current | Motor current (A) | ~4–6 A loaded, ~0 A off |
| COMP | Air intake valve signal | 0 = loading (taking air), 1 = unloaded |
| DV_eletric | Outlet valve control signal | 1 during load |
| Towers | Active dryer tower | alternates on a fixed timer |
| MPG | Starts compressor under load when TP3 < 8.2 bar | |
| LPS | Low-pressure switch | 1 if pressure < 7 bar — **alarm** |
| Pressure_switch | Discharge detected in pilot valve | |
| Oil_level | Oil level switch | 0 = low oil — stop and top up |
| Caudal_impulses | Air flow pulses from the outlet | |

**Duty cycle** = share of time loading. Normal: 20–45 % depending on demand.
**Starts per hour** = number of load cycles. Normal: 4–10.

## 3. Troubleshooting

### 3.1 Air leak (most common fault)
**Symptoms:** duty cycle rises above 50 %; more starts per hour; reservoir pressure falls faster between
cycles; TP3 and Reservoirs average lower; motor current average up because the motor runs longer;
oil temperature creeps up from longer running.
**Likely causes:** leaking pipe joint or hose downstream of reservoirs; failed drain valve stuck open;
worn check-valve seat; leaking pilot valve on consumers.
**Checks:** (1) with consumers isolated, time the pressure decay from 10 to 8 bar; more than 2 bar in
10 minutes confirms a leak; (2) ultrasonic leak detector or soap test on joints, drain valves and the
check valve; (3) inspect dryer purge valve.
**Action:** fix the leak at the source. Running a leaking system for days overheats the compressor
and shortens oil and separator life. Severity: **high** when duty cycle exceeds 70 %.

### 3.2 Separator or filter restriction
**Symptoms:** H1 lower than TP3 by more than 0.5 bar; TP2 higher than normal while loading; oil
temperature up. **Action:** replace separator element / cyclonic filter; check oil carry-over.

### 3.3 Dryer tower fault
**Symptoms:** DV_pressure spikes outside tower changeover; Towers signal not alternating; moisture in
lines. **Action:** check tower solenoids and purge valve; replace desiccant if over 4,000 h.

### 3.4 Overheating
**Symptoms:** Oil_temperature above 85 °C sustained, rising with duty cycle. **Causes:** low oil, cooler
fouling, thermostatic valve stuck, or a leak forcing continuous running. **Action:** stop at 95 °C;
check oil level, clean cooler, test thermostatic valve.

### 3.5 Low pressure alarm
**Symptoms:** LPS = 1, Reservoirs below 7 bar. **Action:** immediate inspection; usually a large leak,
failed intake valve (COMP stuck at 1) or motor trip. Do not dispatch pneumatic consumers.

## 4. Safety rules
- Isolate and depressurise before opening any pressure part. Never loosen fittings under pressure.
- Lock out the motor before work on the compressor stage.
- The copilot gives evidence and suggested checks. **The decision to keep running belongs to the
  maintenance lead.**

## 5. Service intervals
| Item | Interval |
|---|---|
| Leak survey (ultrasonic) | monthly |
| Drain valves check | weekly |
| Oil and oil filter | 2,000 h |
| Separator element | 4,000 h |
| Desiccant | 4,000 h |
| Check valve inspection | 6 months |
