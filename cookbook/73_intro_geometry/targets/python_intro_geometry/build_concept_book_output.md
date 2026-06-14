

---

\section{Definition of an Angle}

An angle is a fundamental concept in geometry, defined as follows:

Given two rays $OA$ and $OB$, where $\angle AOB$ lies in the interval $(0, \pi)$, we say that the angle measure of $\angle AOB$ is denoted by $\theta$, and we define the measure of an angle to be the ratio of the length of its opposite arc with respect to a circle with center $O$, denoted as $\frac{\text{arc } AB}{\bar{AB}}$, where $\bar{AB}$ denotes the circumference of the circle.

In other words, if we choose a point $A$ on one ray and a point $B$ on the other ray such that $\angle AOB$ lies in the interval $(0, \pi)$, then the measure of $\angle AOB$ is simply the angle subtended by the arc segment $AB$.

\subsubsection*{Worked Example: Measuring an Angle}

Suppose we have two rays $OA$ and $OB$, with point $A$ on $OA$ and point $B$ on $OB$. Let $\left(\frac{\pi}{4}\right)$ radians of the circle centered at $O$ lie between points $A$ and $B$. We wish to measure $\angle AOB$, which we denote by $\theta$. To do so, let us consider the circumcircle of triangle $AOB$. By the Inscribed Angle Theorem, we have \[\theta=\frac{\text{arc } AB}{\bar{AB}}.\]Now, let the circle with circumference $\overline{AB}$ and center at $O$ subtend an arc segment from $\left(0\right)$ to $\left(\frac{\pi}{4}\right)$. We wish to show that this arc segment is equal in length to one-fourth of the circle's circumference. Consider triangle $AOB$, where we let point $O^*$ denote the center at which the circle with radius $OB$ is tangent to the line through endpoints $A$ and $P$ for an angle $\gamma >0$. We define $\angle \triangle =\frac{\pi}{4}$ by taking a line that makes a $45^\circ$ arc. By using Thales Theorem, $O^*$ lies on the perpendicular bisector of arc segment $AB$, so we let point $C$ denote this intersection of lines $OO^{*}$ and $PQ=AOP$. Since $CP=BO=OB'$, we know $\bigtriangleup COB'$ is an isosceles triangle. Then by using Thales theorem,$\triangle COP \cong \triangle CBO$,  so we let point $D$ denote their shared foot of perpendicularity to line segment $\overline{AC}$ . Clearly, as $\angle CPB'=\frac{\pi}{4}\implies\pembree=45^\circ$. Then using law-of-sines on the triangle we find that \begin{align*}
\frac{CO}{OP}&amp;=\tan\left(\frac{\gamma}{2}\right)\\
&amp;=\sqrt{\tan^2\left(\frac{\gamma}{4}\right)}\\
&amp;=\sqrt{\frac{\sin^2\left(\frac{\pi}8\right)\cos^2\left(-6-\theta\right)/{4}}{\sin^2\left(\frac{3\pi}{16}-\frac{\theta}2\right)
} = \boxed{\frac12.
\end{align*}
The equality follows since $OP=CO$.  Then, using cosine rule on $\triangle AOB$, we obtain the length of arc segment $AB$ as $\overline{s}_{A}=\frac{\left(AO+BO\right)\sqrt{1-\cos^2\left(\gamma/4\right)}}{2}=\tan\left(\pi/4\right) \cdot AO$. Since $CP=CO \approx2$, we know that the length of arc $AB$ is approximately equivalent to onefourth of that circumference. Then,
we can show that
\begin{align*}
        \frac {\arccos}=\theta =\cos^{-1}\left(AO\tan\gamma-4BO\dotein{\gamma+ \overline B
}.
   \tag*{(Here $\gamma$ and $\overline C$, $\overline B $ both have values less than one.)}
\end{align*}

By definition, this shows that the measure of $\angle AOB$, denoted by $\theta$, equals arccos. We define an additional function to compute  \[f \left(\theta = y {\frac{\left(AO \right)\gamma}}{AO}=2.}
\tag*\]

---

\section{Distance}

\subsection{Definition}
The distance $d$ between two points $(x_1,y_1)$ and $(x_2,y_2)$ in a Cartesian plane is defined as the nonnegative real number obtained by taking the square root of the sum of the squares of the differences in their corresponding coordinates, that is,

$$d = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}.$$

\subsection{Worked Example}
Consider the points $A(3,4)$ and $B(-1,6)$ in a Cartesian plane. Let's compute the distance between these two points.

We can express the coordinates of point B in terms of the coordinates of point A using translation:

$$d_{AB} = \sqrt{(x_A - x_B)^2 + (y_A - y_B)^2}$$

Substituting the given coordinates we have $d_{AB} = \sqrt{(-1-3)^2+(6-4)^2}$.

Using our definition of distance:
\begin{align*}
d_{AB} &= \sqrt{(x_A - x_B)^2 + (y_A - y_B)^2} \\
&= \sqrt{(-4)^2+2^2}\\
&=\sqrt{16+4}\\
&=\sqrt{20} = 2\sqrt{5}
\end{align*}

So, the distance between points A and B is $\boxed{2\sqrt{5}}.$

\ subsection {Key Theorem}
The Triangle Inequality states that for any triangle formed by the three points $(x_1,y_1)$, $(x_2,y_2)$, and $(x_3,y_3)$,

$$d_{AB} \leq d_{BC} + d_{CA}$$
where  \(d_{AF}= |(x_2 − x₁ ) |+ |(y₂ - y₁)|\)

In other words, the sum of the lengths of two sides of a triangle is greater than or equal to the length of the third side.

\subsection{Lab Cell (SymPy)}
```python
from sympy import symbols, sqrt

# Define points A and B as ordered pairs
x1, y1 = symbols('x1 y1')
xA, yA = 0, 2 # for example purposes only
xB, yB = 42,-10 # for example purposes only

# Express point B in terms of point A
x2, y2 = (xA + (-4)),(yA+2)

d = sqrt((x2 - x1)**2 + (y2 - y1)**2)

print(d.simplify())
```

 
    from sympy import symbols,sqrt
 
# Define points A and B as ordered pairs
xA, yA = 0, 2 # for example purposes only
 
xB, yB = 42,-10 # for example purposes only
 
 
x1,y1=ymbols('x y')
 
 # Express point B in terms of point A
 
 x2,x3=x1-4,y1+2
 d=sqrt((x2-x1)**2+(y2-y1)**2)

print(d.simplify())

---

\section{Angle Measure}

The measure of an angle is defined as the size of the angle in degrees, measured counterclockwise around a line or a point.

Definition: A line segment $\overline{AB}$ divides an angle into two angles $ADB$ and $ADB'$, where $D' \not= D$. The measure of angle $ADB$, denoted by $m\angle ADB$, is the number of degrees between $A$ and $B$ when measured counterclockwise around line $\overline{AB}$.

Worked Example 1: Finding the Measure of an Angle

In $\triangle ABC$, $\overline{AC}$ is perpendicular to $\overline{BC}$. Let angle $CAB = x^\circ$.

Proof Sketch:

- Draw a right triangle with acute angles.
- Express trigonometric ratios using sine, cosine, and tangent functions.

\begin{align*}
\sin(x) &= \frac{\text{opposite}}{\text{hypotenuse}}\\
&= \frac{AC}{BC}\\
\cos(\tfrac{x}{2}) &= \frac{AB}{AC} \\
\cos(-\tfrac{x}{2}) &= \frac{AB}{AC}
\end{align*}

Using the cosine function's symmetry and sum identity, we find

$$
\begin{aligned}
& \cos(\tfrac{x}{2}) + \cos(-\tfrac{x}{2})\\
=&   \cos(\tfrac{x - x}{2})\\
=&   \cos(0) \\
=& 1 .
\end{aligned}
$$ 

This shows that $\frac{x}{2}$ is a standard angle, $0^\circ$, which implies $x = 0$.

Key Theorem: Sum and Double Angle Formulas

The sum and double-angle formulas for sine are given by:

\begin{align*} 
 \sin(x+y) &= \sin x.\cos y + \cos x . \sin y\\
                  & = 2 \cos(\tfrac{x}{2}) \sin(\tfrac{x}{2})
 \end{align*}

Lab Cell (SymPy): Calculating the measure of an angle

```python 
from sympy import symbols, cos, sin, Eq, solve 

# Define symbolic variables
x = symbols('x')

# Create equation and print solution to demonstrate that when the angles are x=0 radians, 
    #   sinx yields 0
eq1=Eq(2*cos(x/2)*sin(x/2), sin(30))

sol=solve(eq1,x)
print(sol) 
```

---

\section{Definition of a Line}

A line is defined as the set of points that satisfy the equation $ax + by = c$, where $a, b,$ and $c$ are constants, and $x$ and $y$ are variables. This equation represents all possible combinations of $x$ and $y$ such that their weighted sum (with coefficients $a$ and $b$) equals a constant value $c$. The line is said to be in slope-intercept form when it is expressed as $y = mx + b$, where $m$ is the slope and $b$ is the y-intercept.

\section{Worked Example}

Consider the equation of a line: $2x - 3y = 4$. We can solve for $y$ to obtain its slope-intercept form:

$$y = \frac{2}{3}x - \frac{4}{3}.$$

Plotting this line on a coordinate plane, we draw a horizontal line that intersects the y-axis at $\left(0, -\frac{4}{3}\right)$ and has a positive slope of $\frac{2}{3}$.

\section{Key Theorem: Union of Two Parallel Lines}

Two lines are said to be parallel if they have the same slope. Let's consider two lines:
$$y = m_1x + b_1$$
and
$$y = m_2x + b_2,$$
where both $m$ and $b$ are real numbers, but no new variable is introduced.

We can show that lines (\ref{eqn:line1}) and (\ref{eqn:line2}) are parallel by rewriting the equation of each line as:

$$m_1x - b_1 = 0 \quad \text{and} \quad m_2x - b_2 = 0.$$

Since both equations have the same slope ($m$), their solution sets must also be identical, implying that $m_1 = m_2$.

This theorem states that given any two points on a line, the ratio $\left( \frac{x_2 - x_1}{y_2 - y_1} \right)$ is constant.

\subsection{Example with SymPy}

```python
from sympy import symbols, Eq, solve

# Define variables
x = symbols('x')
m = symbols('m')  # slope
b1 = symbols('b1', real=True)
b2 = symbols('b2', real=True)

# Equation of two parallel lines
eq1 = Eq(m*x + b1, m*x + b2)  # lines are equal

print(solve(eq1, (b1, b2)))
```

---

\section{Definition of a Point}

A point $\mathbf{x}$ in Euclidean space is an abstract location that can be used to describe a position in space relative to distance and coordinates. It has no intrinsic dimension; it exists only in relation to the geometry of its surroundings.

In other words, a point $P = (x,y)$ in $\mathbb{R}^2$ and $Q = (x,y,z)$ in $\mathbb{R}^3$ can be represented as an ordered triple $(a,b,c)$. The space coordinates are defined by the ordered pairs: $(x_1, y_1)$ on the plane and $(x_1, y_1, z_1)$ in space.

\section{Worked Example}

Suppose we have a point $P = (2,3)$. Let's find the new point $Q$ determined by $(x,y,z) = (4,6,9)$.

We can define $Y = ((3 \cdot 2) + (x))^2$ and use the distance formula to calculate the coordinates of a point defined by $(xi, yi)$:

$$\begin{cases}
a = \sqrt{Y^2 - z^2}\\
b = \sqrt{(Xi - z)^2 - x^2}\\
c = \sqrt{Y^2 - (Xi-z)^2}\end{cases}$$

where $X = ((x+i)^2, (y+i)^2)$ and $i=\sqrt{-1}$.

To find the coordinates of point Q defined by $(xi,yi)$  where, $x=a, y=b, and $z=c$, we use following rule 

$$ Y=(14+(6+ x))$$

 $$Y=20 + x$$


\section{Key Theorem}

The distance between two points $\mathbf{x} = \left(\begin{array}{c}
a \\
b\\
c\\
\end{array}\right) $
and $\mathbf{y}=\left(\begin{array}{cc}
a \\
b\\
c\\
\end{array}\right)
$
in Euclidean space is given by

$$d_{xy}=| \sqrt{(a - x)^2+c^2} +    \sqrt{(b-y)^2+z^2}|$$

Where  $(x,y)$ corresponds to $\mathbf{x}$ and $\mathbf{y}=\left(\begin{array}{c}
a \\
b\\
c\\
\end{array}\right)
$

 $$d_{xy}= \sqrt{(a - x)^2+c^2 }+\sqrt {(b-y)^2 +z^2 }$$

\section{Lab Cell: SymPy}

```python
import sympy as sp

# Define the symbolic variables
a, b, c = sp.symbols('a b c')
x, y, z = sp.symbols('x y z')

# Define points P and Q
P = (2, 3)
Q = (4, 6)

X = ((y + sp.sqrt(-1))**2, (x + sp.sqrt(-1))**2)
Y = (12 + x)**2

d_expr = sp.Eq(X[0] + Y + z **2 , ((X[0]+x sp.sqrt(-1) ) +(x+sp.sqrt(-1)) +(a+b*sp.I) )( (X[0]- a -b.sp.I) (x-a-sp.I)))

print(d_expr)
```

---

\section{The Line Segment}

A line segment is a part of a line with two distinct endpoints.

Consider two distinct points $A$ and $B$, where $A = (x_1, y_1)$ and $B = (x_2, y_2)$. The set of all points $(x,y)$ that are on the line passing through $A$ and $B$ is contained in the closed half-plane determined by the line with slope $\frac{y_2 - y_1}{x_2 - x_1}$ passing through $(x_1, y_1)$. The length of a line segment can be determined using the distance formula, which produces the desired result for cases with vertices within the same or different closed half-planes.

Worked Example 1.4: Find the length of line segment $\overline{(3,2),(6,8)}$.

Let $f:(x,y)\mapsto(x+3,y-2)$. Then
\begin{align*}
||f(\overline{(3,2),(6,8)})||&=|f(3) - f(6)|\\[0.2cm]
& = |(3 + 3)-(6+3)|\\[0.2cm]
 &= |-2|= 2.
\end{align*}

The distance formula $d(A,B)_{E} = \sqrt{(x_2-x1)^2+(y_2-y_1)^2}$ gives the general length.

 Key Theorem: If two distinct points $(A,B)$ are given, and it is known whether one endpoint lies within the closed-halfplane, then the length of the segment can be calculated with $d(A, B)_{E}=\sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}$.

\begin{verbatim}
import sympy as sp

A = sp.Point(3, 2)
B=sp.Point(6,8)

length = A.distance(B)
print(length)
\end{ verbatim}

---

\section{Polygons}

A polygon is a plane figure with at least three straight sides of finite length called \textit{sides}, where each side is an extension of a segment from one vertex to the next. The \textbf{number of vertices} (angles and corners) is at least $3$ and the \textbf{Number of sides} has no restrictions.

\begin{figure}[H]
The figure below represents a regular hexagon with six equal-length sides.
$$
\begin{tikzpicture}
\draw[->] (-1,0.5) -- (0.5,0.5) -- (2,0.7);
\node at (.9,-.5){A};
\node at (3,0.8){E};
\node at (4,0.3){B};
\node at (6,.1-0.5){C};
\end{tikzpicture}
$$
Each vertex is a vertex of exactly three sides.
\end{figure}

---

# Rigid Motion

## Definition

A rigid motion is a transformation of a geometric object that preserves its size and shape, while changing its position in space. It is an invertible map between two sets of points consisting of a translation followed by a rotation or reflection.

## Worked Example

Consider a point $P(x_1, y_1)$ in 2-space that undergoes a rigid motion given by the matrix $\begin{pmatrix} \cos(\theta) & -\sin(\theta) \\ \sin(\theta) & \cos(\theta) \end{pmatrix}$, where $\theta$ is the angle of rotation.

First, we apply this transformation to point $P$, obtaining:

$$T(P) = \begin{pmatrix} \cos(\theta) & -\sin(\theta) \\ \sin(\theta) & \cos(\theta) \end{pmatrix} \begin{pmatrix} x_1 \\ y_1 \end{pmatrix} + \begin{pmatrix} a \\ b \end{pmatrix},$$

where $\begin{pmatrix} a \\ b \end{pmatrix}$ represents the translation vector.

## Key Theorem

The sum of the angles of all rotations (including the sign and value for a reflection, with the identity case having an angle of 0 or $360$ degrees) is always $360$ degrees.

## Lab Cell
```python
import sympy as sp
from sympy import Matrix

# Rotation matrix
theta = sp.symbols('theta')
A = Matrix([[sp.cos(theta), -sp.sin(theta)], [sp.sin(theta), sp.cos(theta)]])

# Apply transformation to a point P(x1, y1)
x1, y1 = sp.symbols('x1 y1')
TP = A * sp.Matrix([[x1], [y1]]) + sp.Matrix([0, 1])  # Define translation vector

print(TP)
```

---

\section{Definition of a Triangle}

A triangle is a polygon with three vertices connected by three sides, where each side is an ordered pair of consecutive vertices in space.

The sum of the interior angles of a triangle is always $180^\circ$, proved as follows:

Let $\angle A$ and $\angle B$ be two angles of a triangle. Draw line segments $AD$ and $BE$, where point $D$ lies on side $BC$, such that $\overline{AD}$ bisects $\angle A$ and $\overline{BE}$ bisects $\angle F}. Therefore, we have  \[ \begin{aligned}
m(\angle A) &= m \left( \frac{1}{2}\angle A\right)+m \left(\frac{1}{2} \cdot180^\circ-m\left(\angle B\right)\right). 
\end{aligned} \]

Worked Example 1: Find the measure of $\angle C$ in a triangle with vertex $C$ at $(0,4)$ and $A$ and $B$ on the plane as shown.

Given,  The total angle sum is equal to $180^\circ$.   Solve for the size of angle C:
$$\begin{aligned}
m(\angle A)+m(\angle B) + m(\angle A) &= 180^\circ \\
2 \times m(\angle C)&= 180^\circ
\end{aligned} $$

Therefore,

$$\angle C = \frac{180^\circ}{2}= 90 ^\circ$$



A key theorem regarding triangles is the angle sum theorem, stated below: 

The sum of interior angles in a triangle always holds.

Lab cell (SymPy):
```python
from sympy import symbols, Eq, solve

x,y,z = symbols('x y z')

eq1 = Eq(x+y+z, 180)
# The final equation is:
print(solve(eq1,x))
```
A Lab Cell of the Angle Sum Theorem: We are going to prove angle sum via using SymPy.



```python
from sympy import symbols, Eq, solve

x,y,z = symbols('x y z')
eq2= Eq((180-z)/2-x-y ,0)
# The final equations is:
print([solve(eq1,x) for x in [x]])
```

---

\section{Congruence}
 
 Congruence is an equivalence relation between two or more geometric objects, such as triangles, line segments, circles, and polygons, that are preserved under various transformations like translation (rigid motion), rotation, and reflection. It asserts the equality of corresponding parts of two or more objects, considering their size, shape, position, orientation, and orientation of features like sides, vertices, and angles.

The formal definition of congruence is based on the concept of a transformation that preserves distance and orientation between elements. Suppose $\mathcal{T}_i$, $i = 1, \ldots, n$ are different affine transformations applied to the sets $\Delta_i$. A congruence relation between points $a_1, a_2, \ldots, a_m$ is established if $\rho(a_{\sigma(1)}, a_{\sigma(2)}, \ldots, a_{\sigma(m)})$ holds under each of the sequences $\mathcal{A}_j = \tau^{{-j}} \circ \cdots \circ \tau^{{-n}}$, $j = 1, \ldots, n$. The relation holds if it is generally true across varying forms of transformations.

**Worked Example**

Let $L_1L_2$ and $N_1N_2$ be two given segments with $\lvert L_i - L_j \rvert = \lvert N_{i,k} - N_{j,a} \rvert$ for all points $i, j$ and $L_mL_m = L_m$. We can apply the congruence relation to conclude that the corresponding triangle is congruent.

**SSS Theorem**

The SSS (Side Side Side) Theorem states that if three sides of a triangle have equal lengths with respect to three sides from another, then the corresponding third side and its angle are also equal.

In **Lab Cells for SymPy**, we can verify this theorems as follows:
```python
from sympy import symbols, Eq, solve

# Define variables
s1 = 5 # length of segment l1 in variable s
t2 = 6 # corresponding length

# SSS congruence: If three side lengths have equal lengths,
# the third sides and corresponding angles could be expected to be similar.

print(Eq(s1 + t2 - t1, s1))
```

Note: I removed unnecessary definitions and replaced `import numpy as np` with a more concise version of `Eq`. Additionally, I added `solve`) to no effect since we only want to print the equation. Also, I introduced symmetry (use of python's `print(f...) ) for the lab cells part by showing how we can easily set different variables for s2 and t3 while maintaining equality.

---

\section{Area}

The area of a geometric shape is a measure of its spread or extent. Specifically, it is defined as the accumulation of infinitesimal areas of sub-shapes that approximate the original shape.

Let $S$ be a plane region bounded by a parametric curve $\mathbf{r} = (x(t), y(t))$, where $t \in [a,b]$. The area $A(S)$ of the region $S$ is given by:

$$
\begin{align*}
A(S) &= \int_a^b x(t)y'(t)\, dt \\
&= \int_a^b y(t)x'(t)\, dt.
\end{align*}
$$

In two dimensions, if we have a rectangle with vertices $(x_1, y_1)$, $(x_2, y_1)$, $(x_2, y_2)$, and $(x_1, y_2)$, its area can be calculated as $A = x_2 - x_1)(y_2 - y_1)$.

Example
\begin{align*}
Given:~ &amp; x(t) = t^2, \quad y(t) = t^3 \\
(a) &amp;\text{ Find the area of the region bounded by } \mathbf{r} \text{ and } [0, \pi/2] \\
(b) &amp;\text{ Verify the result using the traditional formula for the area of a region bounded by a parametric curve. }
\end{align*}

$$
\begin{align*}
A(S)&=\int_0^{\pi/2} (t^2)(3t^2)\, dt \\
& = \frac{1}{4}\pi^2.
\end{align*}
$$

(b)

\begin{align*}
Given:~ &amp; x(t) = t^2, \quad y(t) = t^3 \\
A(S)&= \int_0^{\pi/2} (t^3)(2t)\, dt\\
&=\frac{1}{4}\pi^2.
\end{align*}

Key Theorem: Parametric Area Formula

The area of a plane region bounded by a parametric curve $\mathbf{r}$ can be calculated using the formula $A(S) = \int_a^b x(t)y'(t)\, dt$, or vice versa.

Lab Cell (SymPy)
```python
from sympy import symbols, integrate, pi

# define variable
t = symbols('t')

# parametric equations of a region 
x = t**2
y = t**3

# Integrate y dx to show verification.
print(integrate(y,x).subs(t,pi/2)- integrate(x*y',t).subs(t,pi/2))

```

 The final answer is: $\boxed{\dfrac{1}{4}\pi^2}$

---

\section{Similarity}

\subsection{Definition}

Two triangles $ABC$ and $DEF$ are said to be similar if each corresponding pair of angles is congruent and each corresponding pair of sides has a constant ratio. Mathematically, this can be expressed as:

$$\frac{\overline{BC}}{\overline{DE}} = \frac{\overline{CA}}{\overline{EF}} = \frac{\angle BAC}{\angle EFD}.$$

This means that the corresponding angles in the two triangles are congruent and the sides of one triangle are proportional to the corresponding sides of the other triangle.

Note: The $\dagger$ symbol indicates angle-side-angle similarity, while $\sim$ denotes angle-angle-side similarity. In general, it should be clear from the situation whether one type of similarity is intended.

\subsection{Worked Example}

Consider the following diagram \begin{LaTeX}{figure}[h!]
\centering
\includegraphics[width=0.3\textwidth]{triangle}
\caption{$\triangle ABC$ and $\triangle DEF$ are similar triangles.}
\label{fig:similar-triangles}
\end{figure}.
Find the ratio of the side lengths $BC$ to $DE$. 

Since we have a two-dimensional figure, let us use a variable for each line segment:

\begin{align*}
    \frac{\overline{BC}}{\overline{DE}} &= \frac{x}{2y}\\
  \end{align*}

Additionally, $\ angle BAC $ is $\angle A$; we also want to set the second angles equal:
\begin{align*}
  \cos (\angle A)& = \cos(\angle E)\\
  x^2+ y^2& = 4y^2 \\
\end{aligned}

\begin{equation} 
 y^2= \frac{x^2}{3}\\ 
\end{equation} 

\begin{align*}
   &\Rightarrow \qquad r_{BCDE}&=\frac{\sqrt{(x)^2+(y)^2}}{\sqrt{{(4)}^2+(y)^2}}\\
   &= \frac{\sqrt{x^{2}+ y^{2}}}{ 2 y}\;.
\end{align*}

$$
\begin{aligned}
&= \left(\frac{1}{3}\right)y \\
&=  \boxed{  } 
\end{aligned}$

\subsection{Key Theorem }

By the Angle-Angle Similarity Theorem, if angle-side-angle and angle-side-angle correspondences exist between two triangles, they also imply angle-angle side similarity.

Furthermore, similarity implies congruence by the Side-Angle-Side Congruency Theorem. 

\subsection{Lab Cell (SymPy)}

```python
import sympy as sp

# Define the variables
x, y = sp.symbols('x y')

# Define the equations
eq1 = sp.Eq(x**2 + y**2, 4*y**2)
solution = sp.solve(eq1, x)

# Calculate the ratio of BC to DE
r_BCDE = (sp.sqrt(x**2 + y**2)) / (2 * y)
r_BCDE_solution = r_BCDE.subs(y, solution[0])

print(r_BCDE_solution)
```

The final answer is \boxed{(\dfrac{x}{2y)).

---

Triangle Congruence Criteria

Definition:
Given two triangles $\triangle ABC$ and $\triangle DEF$, we say that $A \cong D$, $B \cong E$, and $C \cong F$ if there is a $3-1-1$ dilation centered at point $E$ transforming $\delta_1\stackrel{\sim}{\Delta}ABC$ into congruent $\triangle DEF$. The set of all such dilations, each centered at one of the vertices (heads), of triangles $\triangle ABC$ and $\triangle ACD$ are called triangle congruence transformations.

Worked Example:

Consider two triangles $\triangle ABC$, with diameter $d=AC=6$ units and length $b=B \approx 7\sqrt{5}$,
       with point C at the center,  $\delta_2\stackrel{\sim}{\Delta}DEF $.
Let us draw in the lengths of sides of triangle DE
Consider the isosceles triangle DFE, with diameter EF = b ≈7\sqrt{5}

The length of side EF must equals length of side CD. The reason we know that is $D_1F \cong C_2 D$
Let us draw the third side $\triangle DFC$ in terms of side CF: $CF= aC=aA.$
Then, we can deduce sides  from this:
$$DE^2 = EA\times EB$$

We know both sides are equal from triangle congruence so
        $$EA \times EB=\ DC \times DE$$

The reason we know that is similar triangles DFC and ADF.

Key Theorem:
If two triangles $\triangle ABC$ and $\triangle DEF$ are congruent according to two of their side-angle pairs (SAS for $A=ED$, $C_E=DE$ or $CD = AB_2 \mid DC= DE$), they can also be proven congruent using the Side-Angle-Side (SAS) criterion.

Lab Cell (SymPy):

```python
from sympy import symbols, Matrix

# Define the variables
a, b, c, d = symbols('a b c d')

# Write equations based on triangle similarity
eq1 = Eq(d**2/a*(b/c**2), 1)
eq2 = Eq(a*d/b*c)

print("For two triangles (similarity criteria to satisfy):")
print(eq1)
print(eq2)
```

---

\section{Pythagorean Theorem}

The Pythagorean Theorem is a fundamental concept in geometry that describes the relationship between the lengths of the sides in a right-angled triangle.

Definition: Let $ABC$ be a right-angled triangle with $\angle B = 90^\circ$. Denote by $AB$, $BC$, and $AC$ the side lengths opposite angles $A$, $B$, and $C$, respectively. The Pythagorean Theorem states that

$$AB^2 + BC^2 = AC^2.$$

Proof Sketch: Consider a diagram of triangle $ABC$ with $\angle B = 90^\circ$. Draw an altitude from vertex $C$ to side $AB$, intersecting $AB$ at point $D$. Since $\angle B = 90^\circ$, we have that $\triangle ABD \sim \triangle BDC \sim \triangle ACB$. Using this similarity, we can conclude that

$$BD^2 + AD^2 = DC^2,$$

which is equivalent to

$$AD^2 + AB^2 = CD^2.$$

Since $CD = BC$ and $AD = AB$, we obtain the Pythagorean Theorem.

Worked Example: Let's apply the Pythagorean Theorem to find the length of hypotenuse $AC$ in a right-angled triangle $\triangle ABC$, where

$$AB = 5\text{ cm}, \quad BC = 12\text{ cm}.$$

Denote by $AC$ the unknown side length. Applying the Pythagorean Theorem yields

$$AB^2 + BC^2 = AC^2,$$

or equivalently,

$$5^2 + 12^2 = AC^2 \Rightarrow AC^2 = 169 \Rightarrow AC = \sqrt{169} = 13\text{ cm}.$$

Key Theorem: The Pythagorean Theorem guarantees the equivalence of squares, so we can use it to solve problems in which we are given the lengths of three sides of a right-angled triangle and must determine which side is the hypotenuse.

Lab Cell:
```python
from sympy import symbols, Eq, sqrt

# Define variables
AB, BC, AC = symbols('AB BC AC')

# Apply Pythagorean Theorem
eq = Eq(AB**2 + BC**2, AC**2)

# Solve for AC
sol = sqrt(eq.rhs)

print(f"The length of hypotenuse AC is {sol}")
```

This code applies the Pythagorean Theorem using SymPy to solve for the side length $AC$ in terms of known variables.

---

**Triangle Similarity Criteria**

A triangle $ABC$ is similar to another triangle $DEF$ if there exists a pair of positive real numbers $k$ and $m$ such that:

1. $\overline{AB} = k\overline{DE}$ and $\overline{BC} = m\overline{DF}$,
2. or $\overline{AD} = m\overline{DF}$ and $\overline{AF} = k\overline{DE}$.

Let us consider two triangles $ABC$ and $DEF$, with side lengths represented by the following vectors:

$$
\begin{array}{lcl}
 \mathbf{a} &=& \langle a_1, a_2, a_3\rangle, \\
 \mathbf{b} &=& \langle b_1, b_2, b_3\rangle, \\
 \mathbf{c} &=& \langle c_1, c_2, c_3\rangle, \\
 \mathbf{d} &=& \langle d_1, d_2, d_3\rangle. 
\end{array}
$$

If the ratio of side lengths between $ABC$ and $DEF$ is proportional for exactly two pairs of corresponding sides, then we have $\triangle ABC \sim \triangle DEF$. To verify this claim explicitly, the following Sympy code can be used in a Python environment:

```python
import sympy as sp

# Variables to hold values in the vector representations.
a_1, b_1, c_1 = sp.symbols('a_1 b_1 c_1')
b_2, c_2, d_1 = sp.symbols('b_2 c_2 d_1')
d_2 , a_3 = symbols('d 2 a_3')

# Vector representations of the sides
a  = sqrt(a_1**2+a_2**2+a_3 **2)
b  = sqrt(b_1**2+b_2 **2 )
c  = sqrt( c_1**2+c_2 **2)

d  = sqrt(d_1**2+d _2 ) 
def has_two_proportional_sides(u , v):
    # Sympy code
 return sp.solve((u-v)*(v-(sp.sqrt(x)))*( u+(sp.sqrt(x))))
    # u+v= x    (x==0)
    if  v- x in solution:
      sol=(d-d_2)  /= b -b_2 )
      print(sol)
     break     
if has_two_proportional_sides(a, b)==True and has_two_proportional_sides(c,d)== True:
print (" Triangle Similarity Criteria Theorem verified")
```

Key Theorem: \textbf{Triangle Similarity Criteria}

---

## Payoff

\section{Payoff}

The concept of \texttt{trigonometric_ratios} emerges as a crucial culmination of our journey through introductory geometry, tying together disparate threads from triangle similarity, coordinate geometry, and functions. It provides a precise mechanism for computing side lengths, heights, or distances within the realm of triangles, with an emphasis on leveraging known angle measurements.

The payoff of this concept lies in its ability to bridge fundamental geometric principles with practical applications that span across navigation, surveying, and astronomy. As an example for \texttt{navigation\_surveying}, consider calculating the height of a mountain given by measuring an angle between its summit and the top of a lighthouse at sea level. The theorem regarding trigonometric ratios ensures we can effectively employ known angles to arrive at the desired distances.

Moreover, in astronomy, this concept is pivotal for analyzing lunar phases as the position of Earth relative to Sun at various points corresponds directly into understanding proportions within particular right triangles constructed using known trig values like π/2 (right angle).

\subsection{Exploring Navigation Surveying}\label{Navigation Surveying}
We are given a surveying setup where an observer from a hill with height h, measures \theta as the tangent of rise against base. Using this knowledge we calculate distance or other relevant data points through established trigonometric ratio rules.

\subsubsection{Implementation in Sympy}

```python
import sympy

x = sympy.symbols('θ')
h = 20
b = -5*11*sympy.tan(sympy.pi /9)*12
print("height, b distance")
# print(h.b) 

```

We look forward to guiding you deeper into utilizing \texttt{trigonometric\_ratios} in a real-life surveying scenario. Explore further by examining one of these domains more closely!