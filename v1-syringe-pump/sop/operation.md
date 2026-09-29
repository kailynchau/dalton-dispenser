# Operation SOP

## Preparation

1. Connect the Raspberry Pi to the Arduino with a USB cable.
2. Connect the Raspberry Pi to a monitor over HDMI.
3. Connect a mouse and keyboard to the Raspberry Pi.
4. Use the Arduino IDE to open and upload the Arduino code (`firmware/SerialComm/SerialComm.ino`).
5. Run the GUI: `python3 gui/main.py`

## SU-8

1. Use a Luer-Lok adaptor to attach the prepared SU-8 syringe (see [Fluid Loading SOP](fluid-loading.md)) to the desired microcapillary.
2. Use the optical microscope to move the dispensing tip to the zero position (150 µm to the left of the top-left-most electrode in an 8×8 MED64 array).
3. Press the **SU-8** button under *Select Working Fluid* in the GUI.

## PDMS

1. Raise the plunger using the **Raise Plunger** button.
2. Attach the high-viscosity PDMS syringe and blunt needle to the dispensing head (see [Fluid Loading SOP](fluid-loading.md)).
3. Use the **Dispense** button to lower the plunger until it contacts the syringe head.
4. Zero the dispensing head.
5. Press **Dowsil SE 1700** under *Select Working Fluid*.
6. Raise the plunger again once the system completes operation.
7. Replace the high-viscosity PDMS syringe with its low-viscosity counterpart.
8. Use the **Dispense** button to lower the plunger until it contacts the syringe head.
9. Zero the dispensing head.
10. Press **Sylgard 184** under *Select Working Fluid*.
11. Let the system dispense the fluid.
12. Raise the plunger and remove the loaded syringe.
