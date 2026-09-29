// Include the AccelStepper and MultiStepper Library
#include <AccelStepper.h>
#include <MultiStepper.h>

// pin assignments
int steppersEnablePin = 8;
int xStepPin = 2; //80[steps/mm]
int xDirPin = 5;
int yStepPin = 3; //80[steps/mm]
int yDirPin = 6;
int zStepPin = 4; //400[steps/mm]
int zDirPin = 7;
int pStepPin = 12; // 33960[steps/mm]
int pDirPin = 13;
int xStopPin = 9;
int yStopPin = 10;
int zStopPin = 11;

long positions[4]; // Array of desired stepper positions

String in;
double mode;

int xyzunt = 2;
int punt = 2;

// Define motor interface type
#define motorInterfaceType 1

// Creates an instance
AccelStepper xStepper(motorInterfaceType, xStepPin, xDirPin);
AccelStepper yStepper(motorInterfaceType, yStepPin, yDirPin);
AccelStepper zStepper(motorInterfaceType, zStepPin, zDirPin);
AccelStepper pStepper(motorInterfaceType, pStepPin, pDirPin);

MultiStepper steppers;

void setup()
{
    Serial.begin(9600);
    while (!Serial)
        ;
    Serial.println();

    pinMode(steppersEnablePin, OUTPUT);
    digitalWrite(steppersEnablePin, LOW); // Turn steppers ON by default (HIGH = steppers OFF, LOW = steppers ON)

    // Configure each stepper
    xStepper.setMaxSpeed(1000);
    yStepper.setMaxSpeed(1000);
    zStepper.setMaxSpeed(1000);
    pStepper.setMaxSpeed(2000);

    // Then give them to MultiStepper to manage
    steppers.addStepper(xStepper);
    steppers.addStepper(yStepper);
    steppers.addStepper(zStepper);
    steppers.addStepper(pStepper);

    // For some reasons, the first time moving the motors will end up a small pause, so adding this block to prevent that
    positions[0] = 0;
    positions[1] = 0;
    positions[2] = 0;
    positions[3] = 0;
    steppers.moveTo(positions);
    while (steppers.run())
        ;
    delay(100);

    pinMode(xStopPin, INPUT_PULLUP);
    pinMode(yStopPin, INPUT_PULLUP);
    pinMode(zStopPin, INPUT_PULLUP);
}

void loop()
{

    Serial.println("Please indicate the work mode.");
    Serial.println("1: Manual");
    Serial.println("2: Zeroing");
    Serial.println("3: Mounting");
    Serial.println("4: Calibration");
    Serial.println("5: SU8");
    Serial.println("6: PDMS-1700");
    Serial.println("7: PDMS-184");
    Serial.println();

    mode = UserInput();

    if (mode == 1)
    {
        Serial.println("1: Manual");
        Manual();
    }
    else if (mode == 2)
    {
        Serial.println("2: Zeroing");
        Serial.println("Not Implemented");
        // Zeroing();
        // Serial.println("Done Zeroing\n");
    }
    else if (mode == 3)
    {
        Serial.println("3: Mounting");
        Mounting();
        Serial.println("Done Moving Up\n");
        //    Serial.println("Done Mounting");
    }
    else if (mode == 4)
    {
        Serial.println("4: Calibration");
        Serial.println("Not Implemented");
    }
    else if (mode == 5)
    {
        Serial.println("5: SU8");
        Serial.println("Not Implemented");
    }
    else if (mode == 6)
    {
        Serial.println("6: PDMS-1700");
        PDMS1700();
        Serial.println("Done Dispensing PDMS-1700\n");
    }
    else if (mode == 7)
    {
        Serial.println("7: PDMS-184");
        PDMS184();
        Serial.println("Done Dispensing PDMS-184\n");
    }
    else
    {
        Serial.println("Invalid Input. Please indicate the work mode with.\n");
    }
}

void Manual()
{
    double typ = 1;

    while (typ > 0)
    {
        Serial.println("Please indicate the work type.");
        Serial.println("1: Show Current Position");
        Serial.println("2: Set Zero");
        Serial.println("3: Move");
        Serial.println("4: Multi-Move");
        Serial.println("7: Set Units");
        Serial.println("8: Set Max Speed");
        Serial.println("9: Enable/Disable Motors");
        Serial.println("-1: Exit");
        Serial.println();

        typ = UserInput();

        if (typ <= 0) // consider as Exit
        {
        }
        else if (typ == 1)
        {
            Serial.println("1: Show Current Position (in steps)");
            Serial.print("x:\t");
            Serial.println(xStepper.currentPosition());
            Serial.print("y:\t");
            Serial.println(yStepper.currentPosition());
            Serial.print("z:\t");
            Serial.println(zStepper.currentPosition());
            Serial.print("p:\t");
            Serial.println(pStepper.currentPosition());
            Serial.println();
        }
        else if (typ == 2)
        {
            Serial.println("2: Set Zero");
            SetZero();
            Serial.println("Done setting new zero positions");
            Serial.println();
        }
        else if (typ == 3)
        {
            Serial.println("3: Move (based on current position)");

            Move(1);
        }
        else if (typ == 4)
        {
            Serial.println("4: Multi-Move");

            int num;
            double flag = -1;

            while (flag != 1)
            {
                Serial.println("Please indicate the number of moves.");

                num = UserInput();

                Serial.print("Indicated number of moves:\t");
                Serial.println(num);
                Serial.println();

                Serial.println("Please indicate if that is correct.");
                Serial.println("1: Yes");
                Serial.println("0: No");
                Serial.println();

                flag = UserInput();
            }

            Move(num);
        }
        else if (typ == 7)
        {
            Serial.println("7: Set Units");
            Serial.println("Please indicate the unit for the x, y and z stepper motors.");
            Serial.println("1: step");
            Serial.println("2: mm");
            Serial.println("3: um");
            Serial.println("Resolution: x=y=80, z=400 steps/mm or x=y=12.5, z=2.5 um/step");
            Serial.println();

            xyzunt = UserInput();

            while (xyzunt != 1 && xyzunt != 2 && xyzunt != 3)
            {
                Serial.println("Invalid Input. Please indicate the unit.\n");

                xyzunt = UserInput();
            }

            Serial.print("The unit for the x, y and z stepper motors has been chosen as ");
            if (xyzunt == 1)
            {
                Serial.println("1: step\n");
            }
            else if (xyzunt == 2)
            {
                Serial.println("2: mm\n");
            }
            else if (xyzunt == 3)
            {
                Serial.println("3: um\n");
            }

            Serial.println("Please indicate the unit for the p stepper motor.");
            Serial.println("1: step");
            Serial.println("2: mm");
            Serial.println("3: um");
            Serial.println("Resolution: p=33960 steps/mm or 0.02945 um/step");
            Serial.println();

            punt = UserInput();

            while (punt != 1 && punt != 2 && punt != 3)
            {
                Serial.println("Invalid Input. Please indicate the unit.\n");

                punt = UserInput();
            }

            Serial.print("The unit for the p stepper motor has been chosen as ");
            if (punt == 1)
            {
                Serial.println("1: step\n");
            }
            else if (punt == 2)
            {
                Serial.println("2: mm\n");
            }
            else if (punt == 3)
            {
                Serial.println("3: um\n");
            }
        }
        else if (typ == 8)
        {
            Serial.println("8: Set Max Speed (in steps per sec)");
            Serial.println("Default: x=y=z=1000, p=2000");
            Serial.print("x:\n");
            xStepper.setMaxSpeed(PosUserInput());
            Serial.print("y:\n");
            yStepper.setMaxSpeed(PosUserInput());
            Serial.print("z:\n");
            zStepper.setMaxSpeed(PosUserInput());
            Serial.print("p:\n");
            pStepper.setMaxSpeed(PosUserInput());
            Serial.println();

            Serial.print("Current Max Speed x:\t");
            Serial.println(xStepper.maxSpeed());
            Serial.print("Current Max Speed y:\t");
            Serial.println(yStepper.maxSpeed());
            Serial.print("Current Max Speed z:\t");
            Serial.println(zStepper.maxSpeed());
            Serial.print("Current Max Speed p:\t");
            Serial.println(pStepper.maxSpeed());
            Serial.println();
        }
        else if (typ == 9)
        {
            Serial.println("9: Enable/Disable Motors");
            Serial.println("1: Enable");
            Serial.println("0: Disable");

            if (UserInput() == 1)
            {
                digitalWrite(steppersEnablePin, LOW);
                Serial.println("Motors have been Enabled\n");
            }
            else
            {
                digitalWrite(steppersEnablePin, HIGH);
                Serial.println("Motors have been Disabled\n");
            }
        }
        else
        {
            Serial.println("Invalid Input. Please indicate the work type.\n");
        }
    }
}

void Move(int num)
{
    double flag;
    double locus[num][4];

    for (int ii = 0; ii < num; ii++)
    {
        flag = -1;

        while (flag != 1)
        {
            Serial.print("Please indicate the magnitude for the ");
            Serial.print(ii + 1);
            Serial.println(" move.");
            Serial.print("x (x+:right/x-:left)):\n");
            locus[ii][0] = UserInput();
            Serial.print("y (y+:out/y-:in):\n");
            locus[ii][1] = UserInput();
            Serial.print("z (z+:down/z-:up):\n");
            locus[ii][2] = UserInput();
            Serial.print("p (p+:down/p-:up):\n");
            locus[ii][3] = UserInput();
            Serial.println();

            Serial.println("Indicated Magnitude: x, y, z, p");
            for (int jj = 0; jj < 4; jj++) // 0-3
            {
                Serial.print(locus[ii][jj], 2);
                if (jj < 3)
                {
                    if (xyzunt == 1)
                    {
                        Serial.print("step");
                    }
                    else if (xyzunt == 2)
                    {
                        Serial.print("mm");
                    }
                    else if (xyzunt == 3)
                    {
                        Serial.print("um");
                    }
                    Serial.print(", ");
                }
                else
                {
                    if (punt == 1)
                    {
                        Serial.print("step");
                    }
                    else if (punt == 2)
                    {
                        Serial.print("mm");
                    }
                    else if (punt == 3)
                    {
                        Serial.print("um");
                    }
                }
            }
            Serial.println("\n");

            Serial.println("Please indicate if that is correct.");
            Serial.println("1: Yes");
            Serial.println("0: No");
            Serial.println();

            flag = UserInput();
        }
    }

    // Convert to steps
    if (xyzunt == 2)
    {
        for (int ii = 0; ii < num; ii++)
        {
            locus[ii][0] = locus[ii][0] * 80;
            locus[ii][1] = locus[ii][1] * 80;
            locus[ii][2] = locus[ii][2] * 400;
        }
    }
    else if (xyzunt == 3)
    {
        for (int ii = 0; ii < num; ii++)
        {
            locus[ii][0] = locus[ii][0] * 80 / 1000;
            locus[ii][1] = locus[ii][1] * 80 / 1000;
            locus[ii][2] = locus[ii][2] * 400 / 1000;
        }
    }

    if (punt == 2)
    {
        for (int ii = 0; ii < num; ii++)
        {
            locus[ii][3] = locus[ii][3] * 33960;
        }
    }
    else if (punt == 3)
    {
        for (int ii = 0; ii < num; ii++)
        {
            locus[ii][3] = locus[ii][3] * 33960 / 1000;
        }
    }

    // Everything in steps by now
    flag = 1;
    while (flag == 1)
    {
        Serial.println("Moving. Input anything to stop\n");
        for (int ii = 0; ii < num; ii++)
        {
            RunLocus(locus[ii]);

            if (Serial.available() > 0)
            {
                break;
            }
        }

        if (Serial.available() > 0)
        {
            in = Serial.readStringUntil('\n');
        }

        Serial.println("Please enter 1 if you want to repeat the move.\n");
        flag = UserInput();
    }
}

void RunLocus(double locus[])
{
    long pp = pStepper.maxSpeed() * 0.1;
    if (abs(locus[3]) > pp)
    {
        // Try to remediate the non-stopping behaviour of the P stepper
        long origin[4];
        origin[0] = xStepper.currentPosition();
        origin[1] = yStepper.currentPosition();
        origin[2] = zStepper.currentPosition();
        origin[3] = pStepper.currentPosition();

        if (locus[3] < 0)
        {
            pp = -pp;
        }

        double kk = locus[3] / pp;

        int jj = 0;
        while (jj < kk)
        {
            positions[0] = locus[0] * jj / kk + origin[0];
            positions[1] = locus[1] * jj / kk + origin[1];
            positions[2] = locus[2] * jj / kk + origin[2];
            positions[3] = locus[3] * jj / kk + origin[3];
            steppers.moveTo(positions);

            while (steppers.run() && Serial.available() <= 0)
                ;

            jj++;
        }

        // Last adjustment just in case
        positions[0] = locus[0] + origin[0];
        positions[1] = locus[1] + origin[1];
        positions[2] = locus[2] + origin[2];
        positions[3] = locus[3] + origin[3];
        steppers.moveTo(positions);

        while (steppers.run() && Serial.available() <= 0)
            ;
    }
    else
    {
        positions[0] = locus[0] + xStepper.currentPosition();
        positions[1] = locus[1] + yStepper.currentPosition();
        positions[2] = locus[2] + zStepper.currentPosition();
        positions[3] = locus[3] + pStepper.currentPosition();
        steppers.moveTo(positions);

        while (steppers.run() && Serial.available() <= 0)
            ;
    }
}

// Hard code for now
void PDMS1700()
{
    // steps
    double locus[][4] = {
        {3760, 0, 0, 40000},
        {0, -3760, 0, 22000},
        {-3760, 0, 0, 22000},
        {0, 3600, 0, 22000},
        {3600, 0, 0, 22000},
        {0, 160, 0, 0},
        {0, 0, -1200, 0},
        {-3600, 0, 0, 0},
    };

    Serial.println("Moving. Input anything to stop\n");
    for (int ii = 0; ii < 8; ii++) // Please make sure the number of moves are correct
    {
        RunLocus(locus[ii]);

        if (Serial.available() > 0)
        {
            break;
        }
    }

    if (Serial.available() > 0)
    {
        in = Serial.readStringUntil('\n');
    }
}

// Hard code for now
void PDMS184()
{
    // steps
    double locus[][4] = {
        {5*80, -6*80, 0, 5000},
        {40*80, 0, 0, 40*511.075},
        {0, -38*80, 0, 38*511.075},
        {-40*80, 0, 0, 40*511.075},
        {0, 38*80, 0, 38*511.075},
        {3*80, -3*80, 0, 0},
        {34*80, 0, 0, 34*511.075},
        {0, -32*80, 0, 32*511.075},
        {-34*80, 0, 0, 34*511.075},
        {0, 32*80, 0, 32*511.075},
        {3*80, -3*80, 0, 0},
        {28*80, 0, 0, 28*511.075},
        {0, -26*80, 0, 26*511.075},
        {-28*80, 0, 0, 28*511.075},
        {0, 26*80, 0, 26*511.075},
        {3*80, -3*80, 0, 0},
        {22*80, 0, 0, 22*511.075},
        {0, -20*80, 0, 20*511.075},
        {-22*80, 0, 0, 22*511.075},
        {0, 20*80, 0, 20*511.075},
        {3*80, -3*80, 0, 0},
        {16*80, 0, 0, 16*511.075},
        {0, -14*80, 0, 14*511.075},
        {-16*80, 0, 0, 16*511.075},
        {0, 14*80, 0, 14*511.075},
        {3*80, -3*80, 0, 0},
        {10*80, 0, 0, 10*511.075},
        {0, -8*80, 0, 8*511.075},
        {-10*80, 0, 0, 10*511.075},
        {0, 8*80, 0, 8*511.075},
        {3*80, -3*80, 0, 0},
        {4*80, 0, 0, 4*511.075},
        {0, -2*80, 0, 2*511.075},
        {-4*80, 0, 0, 4*511.075},
        {0, 2*80, 0, 2*511.075},
        {-23*80, 24*80, 0, 0}
    };

    Serial.println("Moving. Input anything to stop\n");
    for (int ii = 0; ii < 36; ii++) // Please make sure the number of moves are correct
    {
        RunLocus(locus[ii]);

        if (Serial.available() > 0)
        {
            break;
        }
    }

    if (Serial.available() > 0)
    {
        in = Serial.readStringUntil('\n');
    }
}

// Would not work for and waiting for updates
void Zeroing()
{
    float DefaultSpeed = 1000;
    float LowSpeed = 10;

    //Save the current max speed for restoring later
    float xMaxSpeed = xStepper.maxSpeed();
    float yMaxSpeed = yStepper.maxSpeed();
    float zMaxSpeed = zStepper.maxSpeed();

    xStepper.setMaxSpeed(DefaultSpeed);
    yStepper.setMaxSpeed(DefaultSpeed);
    zStepper.setMaxSpeed(DefaultSpeed);

    // Move y in
    Serial.println("Moving y stepper. Input anything to stop");
    yStepper.setSpeed(-DefaultSpeed);
    while (digitalRead(yStopPin) == 0 && Serial.available() <= 0)
    {
        yStepper.runSpeed();
    }
    CollectInput();
    // Move y out
    yStepper.setSpeed(LowSpeed);
    while (digitalRead(yStopPin) == 1 && Serial.available() <= 0)
    {
        yStepper.runSpeed();
    }
    CollectInput();
    yStepper.setSpeed(DefaultSpeed);

    // Move x left
    Serial.println("Moving x stepper. Input anything to stop");
    xStepper.setSpeed(-DefaultSpeed);
    while (digitalRead(xStopPin) == 0 && Serial.available() <= 0)
    {
        xStepper.runSpeed();
    }
    CollectInput();
    // Move x right
    xStepper.setSpeed(LowSpeed);
    while (digitalRead(xStopPin) == 1 && Serial.available() <= 0)
    {
        xStepper.runSpeed();
    }
    CollectInput();
    xStepper.setSpeed(DefaultSpeed);

    // Move z down
    Serial.println("Moving z stepper. Input anything to stop");
    xStepper.setSpeed(DefaultSpeed);
    while (digitalRead(zStopPin) == 0 && Serial.available() <= 0)
    {
        zStepper.runSpeed();
    }
    CollectInput();
    // Move z up
    zStepper.setSpeed(-LowSpeed);
    while (digitalRead(zStopPin) == 1 && Serial.available() <= 0)
    {
        zStepper.runSpeed();
    }
    CollectInput();
    zStepper.setSpeed(-DefaultSpeed);

    // Move to the dispensing zero
    //  SetZero();
    //  steppers.moveTo({0,0,0,0});
    //  while (steppers.run())

    SetZero();

    xStepper.setMaxSpeed(xMaxSpeed);
    yStepper.setMaxSpeed(yMaxSpeed);
    zStepper.setMaxSpeed(zMaxSpeed);
}

void SetZero()
{
    xStepper.setCurrentPosition(0);
    yStepper.setCurrentPosition(0);
    zStepper.setCurrentPosition(0);
    pStepper.setCurrentPosition(0);
}

// Waiting for updates
void Mounting()
{
    float DefaultSpeed = 2000;

    //Save the current max speed for restoring later
    float pMaxSpeed = pStepper.maxSpeed();

    pStepper.setMaxSpeed(DefaultSpeed);

    // Move p up
    Serial.println("Moving p stepper. Input anything to stop");
    pStepper.setSpeed(-DefaultSpeed);
    while (Serial.available() <= 0)
    {
        pStepper.runSpeed();
    }
    CollectInput();

    SetZero();

    pStepper.setMaxSpeed(pMaxSpeed);
}

double UserInput()
{
    while (Serial.available() <= 0)
        ;

    in = Serial.readStringUntil('\n');

    return in.toDouble();
}

float PosUserInput()
{
    while (Serial.available() <= 0)
        ;

    in = Serial.readStringUntil('\n');
    float value = in.toFloat();

    while (value <= 0)
    {
        Serial.println("Invalid Input. Please enter a positive value.\n");
        while (Serial.available() <= 0)
            ;

        in = Serial.readStringUntil('\n');
        value = in.toFloat();
    }
    return value;
}

void CollectInput()
{
    if (Serial.available() > 0)
    {
        in = Serial.readStringUntil('\n');
    }
}
