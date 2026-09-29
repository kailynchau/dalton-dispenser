# Assembly SOP

## Preparation

1. Print all provided STL files inside the `Parts` folder (ideally PETG).
2. Assemble the Ender 3 3D printer by following the instructions provided with the printer, with these modifications:
   - Remove the stock aluminum print bed from the Y-axis assembly.
   - Remove the stock electronics case at the front of the printer.
   - Remove the print head and extruder motor from the X-axis.
   - Do not install the filament spool holder or the provided LCD display.

## Syringe Pump Assembly

1. Insert two LM8UU bushings into the plunger holder base.
2. Embed an M5 nut at the top of the plunger holder base.
3. Insert two M3 heat-set inserts into the front of the idler base.
4. Insert two 8 mm smooth rods through the LM8UU bushings inside the plunger holder base.
5. Insert the plunger holder base (with smooth rods) into the idler base.
6. Thread the M5 threaded rod through the M5 nut in the plunger holder base.
7. Attach the M5 threaded rod to the geared stepper motor using a 5 mm to 5 mm coupling.

## Y-Axis Assembly

1. Attach the Y base plate to the Ender 3 Y-axis carriage using 4× M4 bolts.
2. Attach the 4 guide rails into the workpiece fixture base.
3. Feed 2 long (>100 mm) M5 bolts into the 2 channels on the workpiece fixture base, with a nut against the head of each bolt.
4. Place another nut on each bolt on the other side of its channel.
5. Place the 2 moveable MEA supports onto the guide rails and bolts. Hold them in place with 2 more nuts.
6. Attach the workpiece fixture base to the Y base plate using 6× M4 bolts.

## Microscope and Fan Mount Assembly

1. Attach the microscope module to the microscope mount using 4× M2 screws.
2. Insert a carbon filter inside the fan mount.
3. Place the fan inside the fan mount.
4. Join the microscope and fan mounts to Connections A, B, C, and the connection to the Y base plate.
5. Attach the microscope and fan mounts onto the Y base plate.

## Electronics Assembly

Refer to the connection diagram (see the [technical report](../Technical_Design_Report.pdf), Figure 4).

**Arduino pins**

| Feature           | Pin |
|-------------------|-----|
| X end stop switch | 9   |
| Y end stop switch | 10  |
| Z end stop switch | 11  |
| Pico pump         | 48  |
