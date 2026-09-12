# Optimization Formulation & Solver Details

## Problem Formulation
The railway maintenance block scheduling problem is modeled as a Constraint Satisfaction and Optimization Problem using **Google OR-Tools CP-SAT**.

### Time Discretization
- The 24-hour planning horizon is discretized into 15-minute intervals (96 discrete time steps).
- For a task with duration $D$ (in minutes), the duration in discrete intervals is:
  $$\text{intervals} = \lceil D / 15 \rceil$$

### Decision Variables
1. **Window Assignment ($A_{t, w} \in \{0, 1\}$)**: Binary indicator denoting whether task $t$ is scheduled within corridor block window $w$.
2. **Start Time ($S_t \in [0, 96 - \text{intervals}_t]$)**: Integer time step indicating when task $t$ commences execution.
3. **Task Scheduled Indicator ($X_t \in \{0, 1\}$)**:
   $$X_t = \sum_{w \in \mathcal{W}_t} A_{t, w} \le 1$$

---

## Constraints

### 1. Window Boundary Enforcement
If task $t$ is assigned to window $w = [W_w^{\text{start}}, W_w^{\text{end}}]$:
$$S_t \ge W_w^{\text{start}} - M(1 - A_{t, w})$$
$$S_t + \text{intervals}_t \le W_w^{\text{end}} + M(1 - A_{t, w})$$
where $M$ is a sufficiently large constant ($M \ge 96$).

### 2. Departmental Authorization
Task $t$ can only be assigned to window $w$ if department $\text{Dept}_t$ is permitted within window $w$:
$$\text{Dept}_t \in \text{PermittedDepts}_w$$

### 3. Absolute Train Protection (Zero Collisions)
For any scheduled train service $j$ traversing section $\text{Sec}_t$ in time interval $[T_j^{\text{arr}}, T_j^{\text{dep}}]$:
$$(S_t + \text{intervals}_t \le T_j^{\text{arr}}) \lor (S_t \ge T_j^{\text{dep}}) \quad \text{whenever } X_t = 1$$
This is enforced using interval variables and `AddNoOverlap` or Boolean implication constraints, mathematically guaranteeing zero train interference.

### 4. Single Possession Rule
On any given section track, maintenance tasks cannot overlap in time unless approved for coordinated possession:
$$\text{NoOverlap}(\{ \text{Interval}_t \mid \text{Sec}_t = s \})$$

### 5. Department Crew Capacity
For each department $d$, the number of concurrently active maintenance tasks cannot exceed the available field crew gangs:
$$\sum_{t \in \mathcal{T}_d} \mathbb{I}(S_t \le k < S_t + \text{intervals}_t) \le \text{CrewLimit}_d \quad \forall k \in [0, 95]$$

---

## Objective Function

The objective maximizes high-priority task completion while minimizing schedule displacement during re-optimization:

$$\max \sum_{t \in \mathcal{T}} \left( P_t \cdot X_t - C_{\text{dur}} \cdot \text{intervals}_t \cdot X_t - C_{\text{disp}} \cdot |S_t - S_t^{\text{prev}}| \right)$$

Where:
- $P_t$: Priority weight based on urgency:
  - `CRITICAL`: 10,000
  - `HIGH`: 5,000
  - `MEDIUM`: 2,000
  - `LOW`: 500
- $C_{\text{dur}}$: Duration penalty coefficient (encourages compact scheduling).
- $C_{\text{disp}}$: Displacement penalty coefficient (penalizes deviation from previous schedule during emergency re-optimization, ensuring minimal operational disruption).
