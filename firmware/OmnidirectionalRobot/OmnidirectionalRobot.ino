// ==========================================
// MOTOR PINS
// ==========================================

const int FL_EN = 5; const int FL_IN1 = 28; const int FL_IN2 = 29;
const int FR_EN = 4; const int FR_IN1 = 26; const int FR_IN2 = 27;
const int RL_EN = 6; const int RL_IN1 = 24; const int RL_IN2 = 25;
const int RR_EN = 7; const int RR_IN1 = 22; const int RR_IN2 = 23;

// ==========================================
// ENCODER PINS
// ==========================================

const int FL_ENC_A = 18; const int FL_ENC_B = 34;
const int FR_ENC_A = 19; const int FR_ENC_B = 35;
const int RL_ENC_A = 2; const int RL_ENC_B = 36;
const int RR_ENC_A = 3; const int RR_ENC_B = 37;

// ==========================================
// TICK COUNTERS (Volatile for ISRs)
// ==========================================

volatile long ticks_FL = 0;
volatile long ticks_FR = 0;
volatile long ticks_RL = 0;
volatile long ticks_RR = 0;

// ==========================================
// CUSTOM PID CONTROLLER STRUCT
// ==========================================

struct PIDController {
    
    float kp, ki, kd;
    float integral, prev_error;
    long prev_ticks;
    int target_ticks_per_loop;
    
    PIDController(float p, float i, float d) { 
        kp = p; ki = i; kd = d;
        integral = 0; prev_error = 0;
        prev_ticks = 0; target_ticks_per_loop = 0;
    }
    
    int compute(long current_total_ticks) {
        long current_velocity = current_total_ticks - prev_ticks;
        prev_ticks = current_total_ticks;
        float error = target_ticks_per_loop - current_velocity;
        integral += error;
        
        // Anti-Windup / Reset
        if (target_ticks_per_loop == 0) integral = 0;
        if (integral > 1000) integral = 1000;
        if (integral < -1000) integral = -1000;
        
        float derivative = error - prev_error;
        prev_error = error;
        float output = (kp * error) + (ki * integral) + (kd * derivative);

        if (output > 255) output = 255;
        if (output < -255) output = -255;

        return (int)output;   
    }
};

PIDController pid_FL(5.0, 0.5, 0.0);
PIDController pid_FR(5.0, 0.5, 0.0);
PIDController pid_RL(5.0, 0.5, 0.0);
PIDController pid_RR(5.0, 0.5, 0.0);

unsigned long last_pid_time = 0;
unsigned long last_command_time = 0;

void setup() {
    
    Serial.begin(115200);

    // CRITICAL FIX: Stop USB reading from freezing the PID loop
    Serial.setTimeout(10);

    pinMode(FL_EN, OUTPUT); pinMode(FL_IN1, OUTPUT); pinMode(FL_IN2, OUTPUT);
    pinMode(FR_EN, OUTPUT); pinMode(FR_IN1, OUTPUT); pinMode(FR_IN2, OUTPUT);
    pinMode(RL_EN, OUTPUT); pinMode(RL_IN1, OUTPUT); pinMode(RL_IN2, OUTPUT);
    pinMode(RR_EN, OUTPUT); pinMode(RR_IN1, OUTPUT); pinMode(RR_IN2, OUTPUT);
    
    pinMode(FL_ENC_A, INPUT_PULLUP); pinMode(FL_ENC_B, INPUT_PULLUP);
    pinMode(FR_ENC_A, INPUT_PULLUP); pinMode(FR_ENC_B, INPUT_PULLUP);
    pinMode(RL_ENC_A, INPUT_PULLUP); pinMode(RL_ENC_B, INPUT_PULLUP);
    pinMode(RR_ENC_A, INPUT_PULLUP); pinMode(RR_ENC_B, INPUT_PULLUP);
    
    attachInterrupt(digitalPinToInterrupt(FL_ENC_A), isr_FL, RISING);
    attachInterrupt(digitalPinToInterrupt(FR_ENC_A), isr_FR, RISING);
    attachInterrupt(digitalPinToInterrupt(RL_ENC_A), isr_RL, RISING);
    attachInterrupt(digitalPinToInterrupt(RR_ENC_A), isr_RR, RISING); 
}

void loop() {
    
    // READ SERIAL COMMANDS (Non-Blocking & Fragment-Proof)
    if (Serial.available() > 0) {
        String data = Serial.readStringUntil('\n');
    
        int t1, t2, t3, t4;
        
        // Mathematically check that exactly 4 numbers arrived. Throw away broken packets.
        if (sscanf(data.c_str(), "%d,%d,%d,%d", &t1, &t2, &t3, &t4) == 4) {
            pid_FL.target_ticks_per_loop = t1;
            pid_FR.target_ticks_per_loop = t2;
            pid_RL.target_ticks_per_loop = t3;
            pid_RR.target_ticks_per_loop = t4;
            last_command_time = millis(); // Reset safety watchdog
        }
    }
    
    // SAFETY WATCHDOG (Stop if Python crashes or Wi-Fi drops)
    if (millis() - last_command_time > 500) {
        pid_FL.target_ticks_per_loop = 0; 
        pid_FR.target_ticks_per_loop = 0; 
        pid_RL.target_ticks_per_loop = 0; 
        pid_RR.target_ticks_per_loop = 0; 
    }

    // THE 50ms PID TIMING LOOP (Runs strictly at 20Hz)
    if (millis() - last_pid_time >= 50) {
        last_pid_time = millis();

        int pwm_FL = pid_FL.compute(ticks_FL);
        int pwm_FR = pid_FR.compute(ticks_FR);
        int pwm_RL = pid_RL.compute(ticks_RL);
        int pwm_RR = pid_RR.compute(ticks_RR);

        set_motor(FL_EN, FL_IN1, FL_IN2, pwm_FL);
        set_motor(FR_EN, FR_IN1, FR_IN2, pwm_FR);
        set_motor(RL_EN, RL_IN1, RL_IN2, pwm_RL);
        set_motor(RR_EN, RR_IN1, RR_IN2, pwm_RR);

        // Send telemetry back to Python
        
        Serial.print("T,");
        Serial.print(ticks_FL); Serial.print(",");
        Serial.print(ticks_FR); Serial.print(",");
        Serial.print(ticks_RL); Serial.print(",");
        Serial.println(ticks_RR);
    }
}


// ==========================================
// ISRs (Left sides inverted for positive forward counting)
// ==========================================

void isr_FL() { if (digitalRead(FL_ENC_B)) ticks_FL--; else ticks_FL++; }
void isr_FR() { if (digitalRead(FR_ENC_B)) ticks_FR++; else ticks_FR--; }
void isr_RL() { if (digitalRead(RL_ENC_B)) ticks_RL--; else ticks_RL++; }
void isr_RR() { if (digitalRead(RR_ENC_B)) ticks_RR++; else ticks_RR--; }

// ==========================================
// MOTOR DRIVER
// ==========================================

void set_motor(int en_pin, int in1, int in2, int speed) {
    if (speed > 0) {
        digitalWrite(in1, HIGH); digitalWrite(in2, LOW);
    } else if (speed < 0) {
        digitalWrite(in1, LOW); digitalWrite(in2, HIGH);
    } else {
        digitalWrite(in1, LOW); digitalWrite(in2, LOW);
    }
    analogWrite(en_pin, abs(speed));
} 


