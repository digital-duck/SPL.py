

---

Thinking...
Expert linear algebra author.
University textbook.
Precise, formal.
Full definition, proof sketch, concrete worked example.
First-year university student with calculus background.
300–400 words per section.
Definition $\rightarrow$ Worked example $\rightarrow$ Key theorem 
$\rightarrow$ Lab cell (SymPy).
scalar_multiplication.

    *   Definition: Define $k \mathbf{v}$ where $k \in \mathbb{F}$ and 
$\mathbf{v} \in V$. Explain the component-wise definition for 
$\mathbb{R}^n$.
    *   Worked Example: A vector in $\mathbb{R}^3$ multiplied by a scalar 
(e.g., $3 \cdot [1, 2, -4]^T$). Show calculation and result.
    *   Key Theorem: Linearity of scalar multiplication or the property 
$(c \mathbf{u} + d \mathbf{v}) = c\mathbf{u} + d\mathbf{v}$ 
(distributivity/linearity). Let's focus on the distributive laws as they 
are fundamental to vector space axioms.
    *   Lab Cell: SymPy code showing scalar multiplication of a vector in 
$\mathbb{R}^n$.

    *   *Introduction:* Start by defining what it means to scale a vector. 
It is the primary operation for changing magnitude (and direction, if 
negative) while maintaining the orientation along the same line in the 
vector space.

    *   *Definition Section:*
        Let $V$ be a vector space over a field $\mathbb{F}$ (typically 
$\mathbb{R}$ or $\mathbb{C}$). Scalar multiplication is a binary operation 
$\cdot : \mathbb{F} \times V \to V$. For any scalar $\alpha \in 
\mathbb{F}$ and vector $\mathbf{v} \in V$, the product $\alpha \mathbf{v}$ 
results in a new vector in $V$. In the specific case of $\mathbb{R}^n$, if 
$\mathbf{v} = (v_1, v_2, \dots, v_n)$, then:
        $\alpha \mathbf{v} = (\alpha v_1, \alpha v_2, \dots, \alpha v_n)$.

    *   *Worked Example:*
        Let $\mathbf{u} = \begin{bmatrix} 2 \\ -3 \\ 5 \end{bmatrix} \in 
\mathbb{R}^3$. Suppose we wish to scale this vector by the factor $\lambda 
= \frac{1}{2}$.
        Calculation: $\frac{1}{2} \begin{bmatrix} 2 \\ -3 \\ 5 
\end{bmatrix} = \begin{bmatrix} \frac{1}{2}(2) \\ \frac{1}{2}(-3) \\ 
\frac{1}{2}(5) \end{bmatrix} = \begin{bmatrix} 1 \\ -1.5 \\ 2.5 
\end{bmatrix}$.
        The resulting vector points in the same direction as $\mathbf{u}$ 
but has half its original magnitude.

    *   *Key Theorem:*
        Theorem: Linearity of Scalar Multiplication. Let $V$ be a vector 
space over $\mathbb{F}$. For any scalars $\alpha, \beta \in \mathbb{F}$ 
and vectors $\mathbf{u}, \mathbf{v} \in V$:
        1. $\alpha(\mathbf{u} + \mathbf{v}) = \alpha\mathbf{u} + 
\alpha\mathbf{v}$
        2. $(\alpha + \beta)\mathbf{u} = \alpha\mathbf{u} + 
\beta\mathbf{u}$
        *Proof Sketch:* In $\mathbb{R}^n$, these properties follow 
directly from the distributive property of real numbers over addition and 
the component-wise definition of vector addition and scalar 
multiplication.

    *   *Lab Cell (SymPy):* Needs to show `Matrix` or `Vector` 
multiplication by a scalar.

    *   Word count check: The current draft looks like it will land in the 
300-400 range.
    *   Tone: Formal and precise. Use $\mathbb{R}$ for real numbers, etc.
    *   Formatting: LaTeX used correctly.

    *Self-Correction during drafting:* Make sure to emphasize that scalar 
multiplication is a fundamental axiom of vector spaces. The theorem should 
clearly state the distributive properties as they define how scaling 
interacts with addition.
...done thinking.

### Scalar Multiplication

**Definition.** Let $V$ be a vector space over a field $\mathbb{F}$ 
(typically $\mathbb{R}$ or $\mathbb{C}$). Scalar multiplication is a 
binary operation $\cdot: \mathbb{F} \times V \to V$ that associates each 
scalar $\alpha \in \mathbb{F}$ and each vector $\mathbf{v} \in V$ with an 
element $\alpha\mathbf{v} \in V$. In the Euclidean space $\mathbb{R}^n$, 
if a vector is represented as a column of components $\mathbf{v} = 
\begin{bmatrix} v_1 & v_2 & \dots & v_n \end{bmatrix}^T$, then scalar 
multiplication is defined component-wise:
$$\alpha \mathbf{v} = \begin{bmatrix} \alpha v_1 \\ \alpha v_2 \\ \vdots 
\\ \alpha v_n \end{bmatrix}$$
Geometrically, multiplying a vector by a scalar $\alpha$ scales its 
magnitude by $|\alpha|$. If $\alpha > 0$, the direction remains unchanged; 
if $\alpha < 0$, the direction is reversed; and if $\alpha = 0$, the 
result is the zero vector $\mathbf{0}$.

**Worked Example.** Consider a vector $\mathbf{v}$ in $\mathbb{R}^3$ 
representing a physical force, where $\mathbf{v} = \begin{bmatrix} 4 \\ -2 
\\ 6 \end{bmatrix} \text{N}$. Suppose we wish to calculate the effect of 
this force if its magnitude is scaled by a factor of $\frac{3}{2}$.
Applying scalar multiplication:
$$\frac{3}{2}\mathbf{v} = \frac{3}{2} \begin{bmatrix} 4 \\ -2 \\ 6 
\end{bmatrix} = \begin{bmatrix} \frac{3}{2}(4) \\ \frac{3}{2}(-2) \\ 
\frac{3}{2}(6) \end{bmatrix} = \begin{bmatrix} 6 \\ -3 \\ 9 
\end{bmatrix}$$
The resulting vector maintains the same orientation in 
$\mathbb{R}^3$ but possesses a magnitude $1.5$ times larger than the 
original.

**Theorem (Distributivity of Scalar Multiplication).** Let $V$ be a vector 
space over $\mathbb{F}$. For all $\alpha, \beta \in \mathbb{F}$ and 
$\mathbf{u}, \mathbf{v} \in V$, the following identities hold:
1. $\alpha(\mathbf{u} + \mathbf{v}) = \alpha\mathbf{u} + \alpha\mathbf{v}$
2. $(\alpha + \beta)\mathbf{u} = \alpha\mathbf{u} + \beta\mathbf{u}$

*Proof Sketch:* In the coordinate space $\mathbb{R}^n$, these identities 
follow directly from the distributive property of field multiplication 
over addition. Since $( \alpha(u_i + v_i) ) = \alpha u_i + \alpha v_i$ for 
each component $i$, it follows that $\alpha(\mathbf{u} + \mathbf{v}) = 
\alpha\mathbf{u} + \alpha\mathbf{v}$. The second identity follows 
similarly from the field property $(\alpha + \beta)u_i = \alpha u_i + 
\beta u_i$.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define a vector in R^3
v = sp.Matrix([4, -2, 6])
# Define the scalar multiplier
alpha = sp.Rational(3, 2)

# Perform scalar multiplication
result = alpha * v

print(f"Original Vector: {v}")
print(f"Scalar Multiplier: {alpha}")
print(f"Resulting Vector: {result}")
```

---

Thinking...
Expert linear algebra author.
University textbook.
Precise and formal.
Full definition, proof sketch, concrete worked example.
First-year university student with calculus background.
300–400 words per section (Note: I need to ensure the content is dense 
enough but concise enough to stay within or near this limit).

        1. Definition
        2. Worked example
        3. Key theorem
        4. Lab cell (SymPy)
`vector_addition`.
LaTeX for all math, no preamble/metadata.

    *   *Section: Vector Addition.*
    *   *Definition:* Define a vector space $\mathbb{V}$ over a field 
$\mathbb{F}$. Formally define the addition operation $+: \mathbb{V} \times 
\mathbb{V} \to \mathbb{V}$. Mention properties like commutativity, 
associativity, and the existence of an additive identity.
    *   *Worked Example:* Use $\mathbb{R}^n$ (specifically $\mathbb{R}^2$ 
or $\mathbb{R}^3$). Let $\mathbf{u}, \mathbf{v} \in \mathbb{R}^2$. Define 
$\mathbf{u} = (u_1, u_2)$ and $\mathbf{v} = (v_1, v_2)$. Show calculation: 
$\mathbf{w} = \mathbf{u} + \mathbf{v}$.
    *   *Key Theorem:* The property of commutativity or the linearity 
properties. Let's go with the Commutative Property of Vector Addition 
($\mathbf{u} + \mathbf{v} = \mathbf{v} + \mathbf{u}$) as it is 
foundational. Or perhaps a lemma on component-wise addition in 
$\mathbb{R}^n$.
    *   *Lab Cell (SymPy):* Python code using `sympy` to perform vector 
addition of two vectors in 3D space.

    *   *Definition:* Let $V$ be a vector space over a field $\mathbb{F}$. 
Vector addition is a binary operation $+: V \times V \to V$ that maps an 
ordered pair of vectors $(\mathbf{u}, \mathbf{v})$ to a unique sum 
$\mathbf{w} = \mathbf{u} + \mathbf{v}$. For $V$ to qualify as a vector 
space, this operation must satisfy the axioms of an abelian group: (i) 
Associativity: $\mathbf{u} + (\mathbf{v} + \mathbf{w}) = (\mathbf{u} + 
\mathbf{v}) + \mathbf{w}$; (ii) Commutativity: $\mathbf{u} + \mathbf{v} = 
\mathbf{v} + \mathbf{u}$; and (iii) Identity: there exists $\mathbf{0} \in 
V$ such that $\mathbf{u} + \mathbf{0} = \mathbf{u}$. In the standard 
Euclidean space $\mathbb{R}^n$, this addition is defined component-wise: 
if $\mathbf{u} = (u_1, \dots, u_n)$ and $\mathbf{v} = (v_1, \dots, v_n)$, 
then $\mathbf{u} + \mathbf{v} = (u_1+v_1, \dots, u_n+v_n)$.

    *   *Worked Example:* Consider the space $\mathbb{R}^3$. Let 
$\mathbf{u} = \begin{bmatrix} 1 \\ -2 \\ 3 \end{bmatrix}$ and $\mathbf{v} 
= \begin{bmatrix} 4 \\ 5 \\ -1 \end{bmatrix}$. The sum is calculated as:
        $\mathbf{w} = \mathbf{u} + \mathbf{v} = \begin{bmatrix} 1+4 \\ 
-2+5 \\ 3+(-1) \end{bmatrix} = \begin{bmatrix} 5 \\ 3 \\ 2 \end{bmatrix}$.

    *   *Key Theorem:* **Theorem (Commutativity of Vector Addition).** Let 
$V$ be a vector space over $\mathbb{F}$. For any $\mathbf{u}, \mathbf{v} 
\in V$, $\mathbf{u} + \mathbf{v} = \mathbf{v} + \mathbf{u}$.
    *   *Proof Sketch:* In $\mathbb{R}^n$, the proof follows directly from 
the commutativity of addition in $\mathbb{F}$ (typically $\mathbb{R}$). 
Since $\mathbf{u} + \mathbf{v} = (u_1+v_1, \dots, u_n+v_n)$ and $u_i + v_i 
= v_i + u_i$ by field properties, the vectors are identical.

    *   *Lab Cell:* SymPy code for `vector_addition`.

    *   Word count check: The draft is around 250 words. I might need to 
expand the definitions slightly or add detail to ensure it feels "full" 
and hits the target depth of a university textbook.
    *   Refining Definition: Elaborate on the geometric interpretation 
(parallelogram rule) to ensure "depth."

    *Self-Correction during drafting:* Ensure the distinction between 
abstract vector spaces and $\mathbb{R}^n$ is clear, as students often 
confuse general operations with coordinate-wise arithmetic.

    (Drafting final version in LaTeX format).

    *Definition Section:*
    Let $V$ be a set of objects called vectors. The operation of **vector 
addition** is a binary operation $+: V \times V \to V$. For any 
$\mathbf{u}, \mathbf{v} \in V$, the sum $\mathbf{w} = \mathbf{u} + 
\mathbf{v}$ must be an element of $V$. In the context of a vector space 
over a field $\mathbb{F}$, this operation is required to satisfy the 
axioms of an abelian group: it must be closed, associative ($\mathbf{u} + 
(\mathbf{v} + \mathbf{w}) = (\mathbf{u} + \mathbf{v}) + \mathbf{w}$), 
commutative ($\mathbf{u} + \mathbf{v} = \{ \mathbf{v} + \mathbf{u} \}$), 
and possess an additive identity $\mathbf{0} \in V$ such that $\mathbf{u} 
+ \mathbf{0} = \mathbf{u}$. In the Euclidean space $\mathbb{R}^n$, 
addition is performed component-wise: if $\mathbf{u} = (u_1, u_2, \dots, 
u_n)$ and $\mathbf{v} = (v_1, v_2, \dots, v_n)$, then $\mathbf{u} + 
\mathbf{v} = (u_1 + v_1, u_2 + v_2, \dots, u_n + v_n)$.

    *Worked Example:*
    Consider the vector space $\mathbb{R}^3$. Let $\mathbf{u}$ and 
$\mathbf{v}$ be defined as:
    $\mathbf{u} = \begin{bmatrix} 2 \\ -1 \\ 4 \end{bmatrix}, \quad 
\mathbf{v} = \begin{bmatrix} 5 \\ 3 \\ -2 \end{bmatrix}$
    The sum $\mathbf{w} = \mathbf{u} + \mathbf{v}$ is calculated by 
summing corresponding components:
    $\mathbf{w} = \begin{bmatrix} 2+5 \\ -1+3 \\ 4+(-2) \end{bmatrix} = 
\begin{bmatrix} 7 \\ 2 \\ 2 \end{bmatrix}$.

    *Key Theorem:*
    **Theorem (Commutativity of Addition).** Let $V$ be a vector space 
over a field $\mathbb{F}$. For any vectors $\mathbf{u}, \mathbf{v} \in V$, 
the equality $\mathbf{u} + \mathbf{v} = \mathbf{v} + \mathbf{u}$ holds.
    *Proof Sketch:* In the standard coordinate space $\mathbb{R}^n$, this 
property follows from the commutativity of addition in the underlying 
field $\mathbb{F}$. Because $u_i + v_i = v_i + u_i$ for all $1 \leq i \leq 
n$, it follows that $(u_1+v_1, \dots) = (v_1+u_1, \dots)$, thus 
$\mathbf{u} + \mathbf{v} = \mathbf{v} + \mathbf{u}$.

    *Lab Cell:*
    (SymPy code).
...done thinking.

### Vector Addition

**Definition.** Let $V$ be a vector space over a field $\mathbb{F}$. 
**Vector addition** is a binary operation $+: V \times V \to V$ that 
assigns to every pair of vectors $\mathbf{u}, \mathbf{v} \in V$ a unique 
sum $\mathbf{w} = \mathbf{u} + \mathbf{v}$ in $V$. To satisfy the axioms 
of a vector space, this operation must be commutative ($\mathbf{u} + 
\mathbf{v} = \mathbf{v} + \mathbf{u}$) and associative ($\mathbf{u} + 
(\mathbf{v} + \mathbf{w}) = (\mathbf{u} + \mathbf{v}) + \mathbf{w}$), and 
there must exist an additive identity $\mathbf{0} \in V$ such that 
$\mathbf{u} + \mathbf{0} = \mathbf{u}$. In the specific case of the 
Euclidean space $\mathbb{R}^n$, addition is defined component-wise: if 
$\mathbf{u} = (u_1, u_2, \dots, u_n)$ and $\mathbf{v} = (v_1, v_2, \dots, 
v_n)$, then:
$$\mathbf{u} + \mathbf{v} = (u_1 + v_1, u_2 + v_2, \dots, u_n + v_n)$$

**Worked Example.** Consider the vector space $\mathbb{R}^3$. Let 
$\mathbf{u}$ and $\mathbf{v}$ be two vectors representing forces in 
three-dimensional space:
$$\mathbf{u} = \begin{bmatrix} 2 \\ -1 \\ 4 \end{bmatrix}, \quad 
\mathbf{v} = \begin{bmatrix} 5 \\ 3 \\ -2 \end{bmatrix}$$
To find the resultant vector $\mathbf{w} = \mathbf{u} + \mathbf{v}$, we 
sum the corresponding components:
$$\mathbf{w} = \begin{bmatrix} 2+5 \\ -1+3 \\ 4+(-2) \end{bmatrix} = 
\begin{bmatrix} 7 \\ 2 \\ 2 \end{bmatrix}$$

**Key Theorem.** Let $V$ be a vector space over $\mathbb{F}$. For any 
vectors $\mathbf{u}, \mathbf{v} \in V$, the addition is commutative: 
$\mathbf{u} + \mathbf{v} = \mathbf{v} + \mathbf{u}$.
*Proof Sketch:* In $\mathbb{R}^n$, let $\mathbf{u} = (u_1, \dots, u_n)$ 
and $\mathbf{v} = (v_1, \dots, v_n)$. By the definition of component-wise 
addition, $\mathbf{u} + \mathbf{v} = (u_1+v_1, \dots, u_n+v_n)$. Since 
scalar addition in the field $\mathbb{F}$ is commutative ($u_i + v_i = v_i 
+ u_i$), it follows that $(u_1+v_1, \dots) = (v_1+u_1, \dots)$, which is 
the definition of $\mathbf{v} + \mathbf{u}$.

**Lab Cell (SymPy)**
```python
import sympy as sp

def vector_addition(vec1, vec2):
    """
    Performs addition of two vectors in R^n.
    :param vec1: list or tuple representing the first vector
    :param vec2: list or tuple representing the second vector
    :return: SymPy Matrix representing the sum
    """
    v1 = sp.Matrix(vec1)
    v2 = sp.Matrix(vec2)
    return v1 + v2

# Example usage
u = [2, -1, 4]
v = [5, 3, -2]
w = vector_addition(u, v)
print(f"Vector u: {u}")
print(f"Vector v: {v}")
print(f"Sum w:    {w}")
```

---

Thinking...
Expert linear algebra author.
Linear combination (linear\_combination).
University textbook (precise, formal, full definitions, proof sketches, 
concrete examples).
First-year university students with a calculus background.
300-400 words per section.
Definition $\rightarrow$ Worked example $\rightarrow$ Key theorem 
$\rightarrow$ Lab cell (SymPy).

    *   **Definition:** Define it as a linear combination of vectors $v_1, 
\dots, v_n$ with scalars $c_1, \dots, c_n$. Use formal notation.
    *   **Worked Example:** Choose a clear example in $\mathbb{R}^2$ or 
$\mathbb{R}^3$. Maybe something like finding coefficients for specific 
vectors. Actually, the prompt asks for "a concrete worked example". Let's 
use a sum of basis-like vectors to reach a target vector.
    *   **Key Theorem:** Usually, there's no single "theorem" specifically 
*for* the definition itself, but the concept leads to the notion of linear 
dependence or span. However, since I need to stick to the structure: 
Definition $\rightarrow$ Example $\rightarrow$ Key Theorem (Span/Linear 
Independence usually follows), I will frame a theorem regarding the 
existence of coefficients for a specific combination or property of 
linearity. Let's focus on the concept of "Representation as a Linear 
Combination" or the transition to Span.
    *   **Lab Cell (SymPy):** A Python code snippet using SymPy to 
calculate a linear combination.

    *   *Definition:*
        Let $V$ be a vector space over a field $\mathbb{F}$ (typically 
$\mathbb{R}$ or $\mathbb{C}$). Let $\{ \mathbf{v}_1, \mathbf{v}_2, \dots, 
\mathbf{v}_k \}$ be a set of vectors in $V$. A **linear combination** of 
these vectors is an expression of the form:
        $$\mathbf{w} = c_1\mathbf{v}_1 + c_2\mathbf{v}_2 + \dots + 
c_k\mathbf{v}_k$$
        where each $c_i \in \mathbb{F}$ is a scalar. The vectors 
$\mathbf{v}_i$ are the components of the combination, and the scalars 
$c_i$ are known as **coefficients**.

    *   *Worked Example:*
        Let $\mathbf{v}_1 = \begin{pmatrix} 1 \\ 2 \end{pmatrix}$ and 
$\mathbf{v}_2 = \begin{pmatrix} 3 \\ -1 \end{pmatrix}$ in $\mathbb{R}^2$. 
Find the coefficients $c_1, c_2$ such that $\mathbf{w} = \begin{pmatrix} 5 
\\ 4 \end{pmatrix}$ is a linear combination of $\mathbf{v}_1$ and 
$\mathbf{v}_2$.
        We set up the equation: $c_1 \begin{pmatrix} 1 \\ 2 \end{pmatrix} 
+ c_2 \begin{pmatrix} 3 \\ -1 \end{pmatrix} = \begin{pmatrix} 5 \\ 4 
\end{pmatrix}$.
        This results in a system of linear equations:
        $c_1 + 3c_2 = 5$
        $2c_1 - c_2 = 4$
        Multiplying the first by 2 and subtracting gives $6c_2 - c_2 = 10 
- 4 \Rightarrow 5c_2 = 6 \Rightarrow c_2 = 1.2$. Substituting back: $c_1 + 
3(1.2) = 5 \Rightarrow c_1 = 1.4$.
        Thus, $\mathbf{w} = 1.4\mathbf{v}_1 + 1.2\mathbf{v}_2$.

    *   *Key Theorem:* (Focus on Span/Linear Independence). Let's use a 
theorem regarding the existence of coefficients or the property of linear 
independence as it relates to combinations.
        **Theorem:** A vector $\mathbf{w} \in V$ is in the *span* of 
$\{\mathbf{v}_1, \dots, \mathbf{v}_k\}$ if and only if $\mathbf{w}$ can be 
expressed as a linear combination of those vectors.
        (Or perhaps something more specific to "linear combination" 
definition). Let's stick to the standard pedagogical path: The Span.

    *   *Lab Cell (SymPy):* Use `Matrix` or just simple 
addition/multiplication with coefficients.

    *   *Check word count:* Need $\sim 300-400$ words.
    *   *Tone:* Formal and precise.
    *   *Formatting:* LaTeX for math.

    (Self-Correction during drafting): Ensure the distinction between a 
vector being *a* linear combination vs. the set of all possible linear 
combinations (Span) is clear, but focus specifically on the "linear 
combination" component as requested.

    *Drafting Text:*
    **Definition: Linear Combination**
    Let $V$ be a vector space over a field $\mathbb{F}$. Given a finite 
set of vectors $\{\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k\}$ in 
$V$, a **linear combination** of these vectors is an expression of the 
form:
    $$\mathbf{w} = \sum_{i=1}^{k} c_i \mathbf{v}_i = c_1\mathbf{v}_1 + 
c_2\mathbf{v}_2 + \dots + c_k\mathbf{v}_k$$
    where $c_i \in \mathbb{F}$ for each $i \in \{1, \dots, k\}$. The 
elements $c_i$ are called **scalars** or **coefficients**. A linear 
combination provides a way to construct new vectors from a given set by 
scaling and adding them.

    **Worked Example**
    Consider the vector space $\mathbb{R}^2$. Let $\mathbf{v}_1 = 
\begin{bmatrix} 1 \\ 2 \end{bmatrix}$ and $\mathbf{v}_2 = \begin{bmatrix} 
3 \\ -1 \end{bmatrix}$. We wish to determine if the vector $\mathbf{w} = 
\begin{bmatrix} 5 \\ 4 \end{bmatrix}$ can be expressed as a linear 
combination of $\{\mathbf{v}_1, \mathbf{v}_2\}$. This requires finding 
scalars $c_1$ and $c_2$ such that:
    $$c_1 \begin{bmatrix} 1 \\ 2 \end{bmatrix} + c_2 \begin{bmatrix} 3 \\ 
-1 \end{bmatrix} = \begin{bmatrix} 5 \\ 4 \end{bmatrix}$$
    This corresponds to the linear system:
    $$\begin{cases} c_1 + 3c_2 = 5 \\ 2c_1 - c_2 = 4 \end{cases}$$
    By multiplying the first equation by 2, we obtain $2c_1 + 6c_2 = 10$. 
Subtracting the second equation from this result yields $5c_2 = 6$, or 
$c_2 = \frac{6}{5}$. Substituting back into the first equation: $c_1 + 
3(\frac{6}{5}) = 5 \implies c_1 + \frac{18}{5} = \frac{25}{5}$, which 
gives $c_1 = \frac{7}{5}$. Thus, $\mathbf{w}$ is a linear combination of 
$\mathbf{v}_1$ and $\mathbf{v}_2$ with coefficients $c_1 = 1.4$ and $c_2 = 
1.2$.

    **Key Theorem**
    *Theorem:* Let $S = \{\mathbf{v}_1, \dots, \mathbf{v}_k\}$ be a set of 
vectors in $V$. The **span** of $S$, denoted $\text{span}(S)$, is the set 
of all possible linear combinations of the vectors in $S$:
    $$\text{span}(S) = \{ c_1\mathbf{v}_1 + \dots + c_k\mathbf{v}_k \mid 
c_i \in \mathbb{F} \}$$
    A vector $\mathbf{w}$ is said to be linearly dependent on $S$ if it 
can be expressed as a linear combination of the elements in $S$.

    **Lab Cell (SymPy)**
    (Provide Sympy code).

    *Check Word Count:*
    Intro/Def: ~60 words.
    Example: ~140 words.
    Theorem: ~60 words.
    Total text $\approx$ 260-300 range. I might need to beef up the 
definition or theorem slightly to hit the "300-400" range comfortably 
while maintaining precision.

    *Revised Theorem/Span:* Elaborate on the importance of the linear 
combination in defining subspace properties.
    *Revised Definition:* Explicitly state the role of scalars and the 
field $\mathbb{F}$.
...done thinking.

### Linear Combination

**Definition.** Let $V$ be a vector space over a field $\mathbb{F}$ 
(typically $\mathbb{R}$ or $\mathbb{C}$). Given a finite set of vectors 
$\{\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k\}$ in $V$, a **linear 
combination** of these vectors is an expression of the form:
$$\mathbf{w} = c_1\mathbf{v}_1 + c_2\mathbf{v}_2 + \dots + c_k\mathbf{v}_k 
= \sum_{i=1}^{k} c_i \mathbf{v}_i$$
where $c_i \in \mathbb{F}$ for each $i \in \{1, \dots, k\}$. The elements 
$c_1, \dots, c_k$ are referred to as **scalars** or **coefficients**. A 
linear combination represents the construction of a new vector 
$\mathbf{w}$ by scaling each original vector $\mathbf{v}_i$ by its 
corresponding scalar and performing vector addition.

**Worked Example.** Consider the vector space $\mathbb{R}^2$. Let 
$\mathbf{v}_1 = \begin{bmatrix} 1 \\ 2 \end{bmatrix}$ and $\mathbf{v}_2 = 
\begin{bmatrix} 3 \\ -1 \end{bmatrix}$. We wish to determine if the target 
vector $\mathbf{w} = \begin{bmatrix} 5 \\ 4 \end{bmatrix}$ can be 
expressed as a linear combination of $\{\mathbf{v}_1, \mathbf{v}_2\}$. 
This requires finding scalars $c_1$ and $c_2$ such that:
$$c_1 \begin{bmatrix} 1 \\ 2 \end{bmatrix} + c_2 \begin{bmatrix} 3 \\ -1 
\end{bmatrix} = \begin{bmatrix} 5 \\ 4 \end{bmatrix}$$
This vector equation corresponds to the following system of linear 
equations:
$$\begin{cases} c_1 + 3c_2 = 5 \\ 2c_1 - c_2 = 4 \end{cases}$$
Multiplying the first equation by $2$ yields $2c_1 + 6c_2 = 10$. 
Subtracting the second equation from this result gives $(2c_1 - 2c_1) + 
(6c_2 - (-c_2)) = 10 - 4$, which simplifies to $7c_2 = 6$, or $c_2 = 
\frac{6}{7}$. Substituting $c_2$ into the first equation:
$$c_1 + 3\left(\frac{6}{7}\right) = 5 \implies c_1 + \frac{18}{7} = 
\frac{35}{7} \implies c_1 = \frac{17}{7}$$
Thus, $\mathbf{w}$ is a linear combination of $\mathbf{v}_1$ and 
$\mathbf{v}_2$ with coefficients $c_1 = \frac{17}{7}$ and $c_2 = 
\frac{6}{7}$.

**Key Theorem.** The concept of a linear combination is the foundational 
building block for the definition of a **span**. 
*Theorem:* Let $S = \{\mathbf{v}_1, \dots, \mathbf{v}_k\}$ be a set of 
vectors in a vector space $V$. The span of $S$, denoted $\text{span}(S)$, 
is the set of all possible linear combinations of the vectors in $S$:
$$\text{span}(S) = \{ c_1\mathbf{v}_1 + \dots + c_k\mathbf{v}_k \mid c_i 
\in \mathbb{F} \}$$
By definition, $\text{span}(S)$ is the smallest subspace of $V$ containing 
all vectors in $S$. If a vector $\mathbf{w}$ is a linear combination of 
elements in $S$, then $\mathbf{w} \in \text{span}(S)$.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define the basis vectors and the target vector
v1 = sp.Matrix([1, 2])
v2 = sp.Matrix([3, -1])
w = sp.Matrix([5, 4])

# Create a matrix of coefficients (the system)
A = sp.Matrix([[1, 3], [2, -1]])
b = sp.Matrix([5, 4])

# Solve for the scalars c1 and c2
coeffs = A.solve(b)
print(f"Coefficients: c1 = {coeffs[0]}, c2 = {coeffs[1]}")

# Verify the linear combination
linear_comb = coeffs[0]*v1 + coeffs[1]*v2
print(f"Verified linear combination: {linear_comb} == {w}")
```

---

Thinking...
Expert linear algebra author.
Inner Product (inner_product).
University textbook.
Precise, formal.
Full definition, proof sketch, concrete worked example.
First-year university student with calculus background.
300-400 words per section.
Definition $\rightarrow$ Worked example $\rightarrow$ Key theorem 
$\rightarrow$ Lab cell (SymPy).
LaTeX for math. Output only the text.

    *   *Intro/Definition:* Define an inner product space $(V, \langle 
\cdot, \cdot \rangle)$. List the axioms: linearity in the first argument, 
conjugate symmetry (or symmetry in real case), and positive definiteness. 
Specify both real ($\mathbb{R}$) and complex ($\mathbb{C}$) cases briefly 
or focus on $\mathbb{R}$ for simplicity while mentioning the general form.
    *   *Worked Example:* Compute a standard inner product and perhaps a 
weighted inner product to show diversity (e.g., in $\mathbb{R}^2$).
    *   *Key Theorem:* The Cauchy-Schwarz Inequality is the most 
fundamental theorem associated with inner products. It relates the inner 
product to the induced norm.
    *   *Lab Cell:* SymPy code to compute an inner product of two vectors.

    *   *Definition Section:* Use $\langle \cdot, \cdot \rangle$. State 
the four axioms:
        1. Linearity: $\langle au + bv, w \rangle = a\langle u, w \rangle 
+ b\langle v, w \rangle$
        2. Symmetry/Conjugate Symmetry: $\langle u, v \rangle = 
\overline{\langle v, u \rangle}$ (for complex).
        3. Positivity: $\langle v, v \rangle \geq 0$.
        4. Definiteness: $\langle v, v \rangle = 0 \iff v = 0$.
    *   *Worked Example:* Let $V = \mathbb{R}^2$. Define $\langle 
\mathbf{u}, \mathbf{v} \rangle = u_1 v_1 + 2u_2 v_2$. Calculate for 
$\mathbf{u}=(1,2)$ and $\mathbf{v}=(3,1)$.
    *   *Key Theorem:* Cauchy-Schwarz: $|\langle \mathbf{u}, \mathbf{v} 
\rangle| \leq \|\mathbf{u}\| \|\mathbf{v}\|$. Mention that it leads to the 
Triangle Inequality.
    *   *Lab Cell:* Use SymPy's `Matrix` or just symbolic variables to 
show a manual calculation of an inner product.

    *   *Word count check:* Need 300-400 words for the section.
    *   *Refining the definition:* Make it formal. "An inner product is a 
function $\langle \cdot, \cdot \rangle: V \times V \to \mathbb{F}$..."
    *   *Refining the Theorem:* Cauchy-Schwarz is perfect because it links 
geometry (angle/length) to algebra.

    *Drafting content:*
    **Definition: The Inner Product**
    Let $V$ be a vector space over a field $\mathbb{F}$ (where 
$\mathbb{F}$ is either $\mathbb{R}$ or $\mathbb{C}$). An **inner product** 
is a function $\langle \cdot, \cdot \rangle : V \times V \to \mathbb{F}$ 
that maps each pair of vectors $(\mathbf{u}, \mathbf{v})$ to a scalar such 
that the following axioms hold for all $\mathbf{u}, \mathbf{v}, \mathbf{w} 
\in V$ and $c \in \mathbb{F}$:
    1. Linearity in the first argument: $\langle c\mathbf{u} + \mathbf{v}, 
\mathbf{w} \rangle = c\langle \mathbf{u}, \mathbf{w} \rangle + \langle 
\mathbf{v}, \mathbf{w} \rangle$.
    2. Conjugate Symmetry: $\langle \mathbf{u}, \mathbf{v} \rangle = 
\overline{\langle \mathbf{v}, \mathbf{u} \rangle}$. (Note: If 
$\mathbb{F}=\mathbb{R}$, this simplifies to symmetry, $\langle \mathbf{u}, 
\mathbf{v} \rangle = \langle \mathbf{v}, \mathbf{u} \rangle$).
    3. Positive Definiteness: $\langle \mathbf{u}, \mathbf{u} \rangle \geq 
0$, and $\langle \mathbf{u}, \mathbf{u} \rangle = 0$ if and only if 
$\mathbf{u} = \mathbf{0}$.

    **Worked Example**
    Consider the vector space $\mathbb{R}^2$ with a weighted inner product 
defined by $\langle \mathbf{u}, \mathbf{v} \rangle = u_1 v_1 + 2u_2 v_2$. 
Let $\mathbf{u} = (1, 3)$ and $\mathbf{v} = (2, -1)$.
    Calculation:
    $\langle \mathbf{u}, \mathbf{v} \rangle = (1)(2) + 2(3)(-1) = 2 - 6 = 
-4$.
    To find the norm $\|\mathbf{u}\| = \sqrt{\langle \mathbf{u}, 
\mathbf{u} \rangle}$:
    $\|\mathbf{u}\| = \sqrt{(1)^2 + 2(3)^2} = \sqrt{1+18} = \sqrt{19}$.

    **Key Theorem: The Cauchy-Schwarz Inequality**
    For any vectors $\mathbf{u}, \mathbf{v}$ in an inner product space $V$ 
over $\mathbb{R}$, the following inequality holds:
    $$|\langle \mathbf{u}, \mathbf{v} \rangle| \leq \|\mathbf{u}\| 
\|\mathbf{v}\|$$
    *Proof Sketch:* Consider the quadratic form $f(t) = \| \mathbf{u} + 
t\mathbf{v} \|^2$. Since $f(t) \geq 0$ for all $t$, its discriminant as a 
polynomial in $t$ must be non-positive. Expanding using the inner product 
properties leads directly to the inequality.

    **Lab Cell (SymPy)**
    ```python
    import sympy
    # Define vectors and the inner product function
    u = sympy.Matrix([1, 3])
    v = sympy.Matrix([2, -1])
    # Weighted metric matrix M = [[1, 0], [0, 2]]
    M = sympy.Matrix([[1, 0], [0, 2]])
    inner_prod = u.T * M * v
    print(f"Inner Product: {inner_prod}")
    ```

    Wait, I need to ensure the word count is high enough (300-400 words). 
The current draft might be a bit short. Let me expand on the definition of 
Norm and the significance of Cauchy-Schwarz.

    *Expanding Definition:* Add detail about why $\mathbb{F} = \mathbb{C}$ 
requires conjugate symmetry to ensure real values for $\|v\|$.
    *Expanding Theorem:* Mention how it leads to the definition of the 
angle $\theta$.

    Let's re-calculate words:
    Intro/Def: ~100 words.
    Example: ~80 words.
    Theorem: ~120 words.
    Lab Cell: Not counted usually but let's assume 50 for description. 
Total around 350. Perfect.

    Wait, I need to be careful with LaTeX formatting in the prompt "Output 
only the section text".

    *Self-Correction on Example:* Ensure it clearly distinguishes between 
standard dot product and a generalized inner product.
    *Self-Correction on Theorem:* Cauchy-Schwarz is essential.

    Let's refine the structure:
    Definition: $V, \mathbb{F},$ axioms (Lineatiry, Conjugate Symmetry, 
Positivity).
    Worked Example: $\mathbb{R}^n$ with a non-standard inner product to 
show it's not just a dot product.
    Theorem: Cauchy-Schwarz. Explain $\|x\| = \sqrt{\langle x, x 
\rangle}$.
    Lab Cell: SymPy calculation.

    *Final check of requirements:* "No preamble, no metadata." -> Only the 
content starting from Definition.
...done thinking.

### Definition: The Inner Product

Let $V$ be a vector space over a field $\mathbb{F}$, where $\mathbb{F}$ is 
typically the field of real numbers $\mathbb{R}$ or complex numbers 
$\mathbb{C}$. An **inner product** on $V$ is a function $\langle \cdot, 
\cdot \rangle: V \times V \to \mathbb{F}$ that maps every pair of vectors 
$(\mathbf{u}, \mathbf{v})$ to a scalar in $\mathbb{F}$, satisfying the 
following axioms for all $\mathbf{u}, \mathbf{v}, \mathbf{w} \in V$ and $c 
\in \mathbb{F}$:

1.  **Linearity in the first argument**: $\langle c\mathbf{u} + 
\mathbf{v}, \mathbf{w} \rangle = c\langle \mathbf{u}, \mathbf{w} \rangle + 
\langle \mathbf{v}, \mathbf{w} \rangle$.
2.  **Conjugate Symmetry**: $\langle \mathbf{u}, \mathbf{v} \rangle = 
\overline{\langle \mathbf{v}, \mathbf{u} \rangle}$. (Note: If $\mathbb{F} 
= \mathbb{R}$, this implies symmetry, $\langle \mathbf{u}, \mathbf{v} 
\rangle = \langle \mathbf{v}, \mathbf{u} \rangle$).
3.  **Positive Definiteness**: $\langle \mathbf{u}, \mathbf{u} \rangle 
\geq 0$ for all $\mathbf{u} \in V$, and $\langle \mathbf{u}, \mathbf{u} 
\rangle = 0$ if and only if $\mathbf{u} = \mathbf{0}$.

An inner product space is a pair $(V, \langle \cdot, \cdot \rangle)$ 
consisting of a vector space $V$ equipped with an inner product. The 
standard inner product on $\mathbb{R}^n$ is the dot product: $\langle 
\mathbf{u}, \mathbf{v} \rangle = \sum_{i=1}^n u_i v_i$.

### Worked Example
Consider the vector space $V = \mathbb{R}^2$ equipped with a weighted 
inner product defined by the bilinear form:
$$\langle \mathbf{u}, \mathbf{v} \rangle = u_1 v_1 + 2u_2 v_2$$
Let $\mathbf{u} = (1, 3)$ and $\mathbf{v} = (2, -1)$. We calculate the 
inner product:
$$\langle \mathbf{u}, \mathbf{v} \rangle = (1)(2) + 2(3)(-1) = 2 - 6 = 
-4$$
To find the induced norm $\|\mathbf{u}\| = \sqrt{\langle \mathbf{u}, 
\mathbf{u} \rangle}$ of $\mathbf{u}$:
$$\|\mathbf{u}\| = \sqrt{(1)^2 + 2(3)^2} = \sqrt{1 + 18} = \sqrt{19}$$

### Key Theorem: The Cauchy-Schwarz Inequality
For any vectors $\mathbf{u}, \mathbf{v}$ in an inner product space over 
$\mathbb{R}$, the following inequality holds:
$$|\langle \mathbf{u}, \mathbf{v} \rangle| \leq \|\mathbf{u}\| 
\|\mathbf{v}\|$$
*Proof Sketch:* Consider the quadratic form $f(t) = \| \mathbf{u} + 
t\mathbf{v} \|^2$. By the property of positive definiteness, $f(t) \geq 0$ 
for all $t \in \mathbb{R}$. Expanding this using linearity and symmetry 
gives $f(t) = \langle \mathbf{u}, \mathbf{u} \rangle + 2t\langle 
\mathbf{u}, \mathbf{v} \rangle + t^2\langle \mathbf{v}, \mathbf{v} 
\rangle$. Since this is a quadratic in $t$ with a non-negative leading 
coefficient, its discriminant must be non-positive: $(2\langle \mathbf{u}, 
\mathbf{v} \rangle)^2 - 4\langle \mathbf{u}, \mathbf{u} \rangle \langle 
\mathbf{v}, \mathbf{v} \rangle \leq 0$. Dividing by 4 and taking the 
square root yields the result.

### Lab cell (SymPy)
```python
import sympy
from sympy import Matrix

# Define vectors in R^2
u = Matrix([1, 3])
v = Matrix([2, -1])

# Define a weighted inner product using a metric matrix M
# This represents the weights [1, 0; 0, 2] from our example
M = Matrix([[1, 0], [0, 2]])

def inner_product(vec1, vec2, metric):
    return vec1.T * metric * vec2

# Calculation
result = inner_product(u, v, M)
print(f"The inner product <u, v> is: {result}")
```

---

Thinking...
Expert linear algebra author.
University textbook (precise, formal).
First-year university student with calculus background.
Linear independence ($linear\_independence$).
Definition $\to$ Worked Example $\to$ Key Theorem $\to$ Lab Cell (SymPy).

        *   Length: 300–400 words per section (total for the specific 
topic area).
        *   Formatting: LaTeX for all math.
        *   Content: Full definition, proof sketch (implied in "Key 
theorem" or derivation), concrete example.
        *   Output constraints: Only the section text. No 
preamble/metadata.

    *   *Definition:* A set of vectors $\{v_1, \dots, v_k\}$ is linearly 
independent if $c_1 v_1 + \dots + c_k v_k = 0$ implies $c_i = 0$ for all 
$i$. Otherwise, they are linearly dependent.
    *   *Worked Example:* Need a concrete vector space (e.g., 
$\mathbb{R}^3$). Vectors: $v_1 = (1, 0, 1)$, $v_2 = (0, 1, 1)$. Check 
independence. Or perhaps three vectors to show dependence? Let's go with 
two independent vectors in $\mathbb{R}^3$ or three dependent ones. 
Actually, a set like $\{(1, 2), (3, 4)\}$ vs $\{(1, 2), (2, 4)\}$.
    *   *Key Theorem:* Relation to spanning sets/basis or the "Linear 
Combination" property. A common theorem is: "A set of $n$ vectors in 
$\mathbb{R}^m$ where $n > m$ is always linearly dependent." Or perhaps the 
characterization of a basis component. Let's go with the theorem relating 
linear independence to the trivial solution of a homogeneous system $Ax = 
0$.
    *   *Lab Cell:* SymPy code to check rank or solve the equation.

    *   *Section Header:* Linear Independence.
    *   *Definition:* Define $\mathcal{V}$ as a vector space over field 
$\mathbb{F}$. Definition of linear independence: $c_1 \mathbf{v}_1 + \dots 
+ c_k \mathbf{v}_k = \mathbf{0} \implies c_i=0$.
    *   *Worked Example:* Let $\mathbf{v}_1 = (1, 2, 3)^T$ and 
$\mathbf{v}_2 = (4, 5, 6)^T$. Check if $c_1\mathbf{v}_1 + c_2\mathbf{v}_2 
= \mathbf{0}$. Solve the system.
    *   *Key Theorem:* A set of vectors is linearly independent if and 
only if the matrix formed by these vectors has full column rank (i.e., its 
columns are not linear combinations of each other). Alternatively, a set 
of $n$ vectors in $\mathbb{R}^m$ where $n > m$ must be linearly dependent. 
Let's go with the "Linear Dependence" implication: if one vector is a 
linear combination of others.

    *   Length check: Target 300-400 words.
    *   Tone: Formal/Precise. Use symbols like $\mathbb{F}$, $\in$, 
$\implies$.
    *   LaTeX usage: ensure all variables and formulas are in $...$ or 
$$...$$.

    *Drafting the content:*
    **Definition.** Let $V$ be a vector space over a field $\mathbb{F}$. A 
set of vectors $\{\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k\} 
\subseteq V$ is said to be **linearly independent** if the only scalars 
$c_1, c_2, \dots, c_k \in \mathbb{F}$ satisfying the equation
    $$\sum_{i=1}^k c_i \mathbf{v}_i = \mathbf{0}$$
    are $c_1 = c_2 = \dots = c_k = 0$. If there exists at least one 
non-zero scalar $c_j$ such that the equality holds, the set is **linearly 
dependent**.

    *Worked Example:* Consider the vectors $\mathbf{u} = \begin{pmatrix} 1 
\\ 2 \end{pmatrix}$ and $\mathbf{v} = \begin{pmatrix} 3 \\ 4 
\end{pmatrix}$ in $\mathbb{R}^2$. To test for linear independence, we set 
up the vector equation $c_1\mathbf{u} + c_2\mathbf{v} = \mathbf{0}$. This 
yields the system:
    $$\begin{cases} 1c_1 + 3c_2 = 0 \\ 2c_1 + 4c_2 = 0 \end{cases}$$
    Subtracting twice the first equation from the second gives $2c_2 = 0$, 
implying $c_2=0$. Substituting back, we find $c_1=0$. Since both constants 
must be zero, $\{\mathbf{u}, \mathbf{v}\}$ is linearly independent. 
Conversely, $\{ (1, 2), (2, 4) \}$ is dependent because $2(1, 2) - 1(2, 4) 
= 0$ does not require coefficients to be zero.

    *Key Theorem:* Let $\mathbf{A} \in \mathbb{R}^{m \times n}$ be a 
matrix whose columns are vectors $\{\mathbf{a}_1, \dots, \mathbf{a}_n\}$. 
The set of columns is linearly independent if and only if the null space 
of $\mathbf{A}$ contains only the zero vector ($\text{null}(\mathbf{A}) = 
\{\mathbf{0}\}$). This occurs precisely when $\text{rank}(\mathbf{A}) = 
n$. A critical corollary: any set of $n$ vectors in $\mathbb{R}^m$ where 
$n > m$ is necessarily linearly dependent.

    *Lab Cell:* (SymPy code)
    ```python
    import sympy as sp
    # Define the matrix representing the vectors
    A = sp.Matrix([[1, 3], [2, 4]])
    # Check rank vs number of columns
    rank_val = A.rank()
    print(f"Rank: {rank_val}")
    is_independent = rank_val == A.ncols
    print(f"Are the columns linearly independent? {is_independent}")
    ```

    *Word count check:* Around 320 words. Perfect.
    *Style check:* Formal. "Let $V$ be...", "Suppose...". LaTeX is 
correct. Structure matches exactly.

    Wait, let me refine the "Key Theorem" to make it more robust for a 
university student's introduction. The connection between linear 
independence and the rank of a matrix is standard in first-year courses. 
Let's ensure the distinction between "independent" and "dependent" is 
clear.

    Refining the logic:
    1. Definition (Linear Independence)
    2. Worked Example (Two vectors in $\mathbb{R}^2$)
    3. Key Theorem (Relation to rank/matrix dimensions)
    4. Lab cell.

    Final check on "Proof sketch" requirement from prompt: "full 
definition, proof sketch, concrete worked example". The prompt asks for a 
"proof sketch" in the style guide but the structure list is "Definition 
$\to$ Worked example $\to$ Key theorem $\to$ Lab cell". I will include a 
brief logical justification or derivation within the Theorem section to 
satisfy the "proof sketch" requirement of the style.

    *Refining Definition:*
    **Definition: Linear Independence.** Let $V$ be a vector space over a 
field $\mathbb{F}$. A set of vectors $\{\mathbf{v}_1, \dots, 
\mathbf{v}_k\} \in V$ is **linearly independent** if the equation 
$\sum_{i=1}^k c_i \mathbf{v}_i = \mathbf{0}$ implies $c_j = 0$ for all $j 
\in \{1, \dots, k\}$. If there exists a set of coefficients $\{c_1, \dots, 
c_k\}$ not all zero such that $\sum_{i=1}^k c_i \mathbf{v}_i = 
\mathbf{0}$, the set is **linearly dependent**.

    *Refining Theorem:*
    **Theorem.** Let $A$ be an $m \times n$ matrix whose columns are the 
vectors $\{\mathbf{a}_1, \dots, \mathbf{a}_n\}$. The columns are linearly 
independent if and only if $\text{rank}(A) = n$.
    *Proof Sketch:* If $\text{rank}(A) < n$, there exists a non-trivial 
solution to $Ax=0$ by the Rank-Nullity Theorem, implying linear 
dependence. If $\text{rank}(A) = n$, the column space has dimension $n$, 
and no vector can be formed as a combination of others.

    *Word count check again:*
    Approx 350 words. Good.
...done thinking.

**Definition: Linear Independence**

Let $V$ be a vector space over a field $\mathbb{F}$ (typically 
$\mathbb{R}$ or $\mathbb{C}$). A finite set of vectors $\{\mathbf{v}_1, 
\mathbf{v}_2, \dots, \mathbf{v}_k\} \subseteq V$ is said to be **linearly 
independent** if the only solution to the vector equation
$$\sum_{i=1}^k c_i \mathbf{v}_i = \mathbf{0}$$
is the trivial solution $c_1 = c_2 = \dots = c_k = 0$, where each $c_i \in 
\mathbb{F}$. If there exists at least one set of scalars $\{c_1, \dots, 
c_k\}$, not all of which are zero, such that the sum equals the zero 
vector, then the set is said to be **linearly dependent**. Geometrically, 
linear dependence implies that at least one vector in the set can be 
expressed as a linear combination of the others.

**Worked Example**

Consider the set of vectors $\{\mathbf{v}_1, \mathbf{v}_2\}$ in 
$\mathbb{R}^3$:
$$\mathbf{v}_1 = \begin{pmatrix} 1 \\ 0 \\ 1 \end{pmatrix}, \quad 
\mathbf{v}_2 = \begin{pmatrix} 0 \\ 1 \\ 1 \end{pmatrix}$$
To test for linear independence, we set up the equation $c_1\mathbf{v}_1 + 
c_2\mathbf{v}_2 = \mathbf{0}$:
$$c_1 \begin{pmatrix} 1 \\ 0 \\ 1 \end{pmatrix} + c_2 \begin{pmatrix} 0 \\ 
1 \\ 1 \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \\ 0 \end{pmatrix}$$
This yields a system of linear equations:
$$ \begin{cases} c_1 = 0 \\ c_2 = 0 \\ c_1 + c_2 = 0 \end{cases} $$
From the first two equations, we see $c_1=0$ and $c_2=0$. Since the only 
solution is the trivial one, the set $\{\mathbf{v}_1, \mathbf{v}_2\}$ is 
linearly independent. In contrast, for $\mathbf{u}_1 = (1, 2)$ and 
$\mathbf{u}_2 = (2, 4)$, we find $2\mathbf{u}_1 - 1\mathbf{u}_2 = 
\mathbf{0}$, hence $\{\mathbf{u}_1, \mathbf{u}_2\}$ is linearly dependent.

**Key Theorem**

**Theorem.** Let $A$ be an $m \times n$ matrix whose columns 
$\mathbf{a}_1, \dots, \mathbf{a}_n$ are vectors in $\mathbb{R}^m$. The set 
of columns $\{\mathbf{a}_1, \dots, \mathbf{a}_n\}$ is linearly independent 
if and only if the rank of $A$ is equal to $n$ (i.e., $A$ has full column 
rank).

*Proof Sketch:* By the Rank-Nullity Theorem, $\dim(\text{null}(A)) = n - 
\text{rank}(A)$. If $\text{rank}(A) = n$, then $\dim(\text{null}(A)) = 0$. 
This implies that the only vector $\mathbf{x}$ satisfying $A\mathbf{x} = 
\mathbf{0}$ is $\mathbf{x} = \mathbf{0}$, which is the definition of 
linear independence for the columns. If $\text{rank}(A) < n$, then there 
exists a non-zero vector in the null space, implying linear dependence.

**Lab Cell (SymPy)**

```python
import sympy as sp

# Define a matrix where columns represent vectors in R^3
# Example: v1 = [1, 0, 1], v2 = [0, 1, 1]
A = sp.Matrix([[1, 0], 
                [0, 1], 
                [1, 1]])

# Calculate the rank of the matrix
rank_val = A.rank()

# A set is linearly independent if rank == number of columns
is_independent = (rank_val == A.ncols)

print(f"Matrix Rank: {rank_val}")
print(f"Number of Columns: {A.ncols}")
print(f"Are the vectors linearly independent? {is_independent}")
```

---

Thinking...
Expert linear algebra author.
University textbook (precise, formal).
First-year university student with calculus background.
`linear_map`.
Definition $\rightarrow$ Worked example $\rightarrow$ Key theorem 
$\rightarrow$ Lab cell (SymPy).
300–400 words per section (total, or for this specific concept? Usually 
implies the whole section should be in that range).
LaTeX for all math. Output *only* the content.

    *   *Definition:* A function $T: V \to W$ is a linear map if $T(u + v) 
= T(u) + T(v)$ and $T(cu) = cT(u)$. Need to specify vector spaces.
    *   *Worked Example:* Let $V = \mathbb{R}^2$, $W = \mathbb{R}^1$. 
Define $T(x, y) = x + 2y$. Show linearity. Or something slightly more 
abstract like a transformation of polynomials. Let's stick to 
$\mathbb{R}^n$ but maybe use a matrix representation.
    *   *Key Theorem:* The fundamental property that linear maps are 
determined by their action on a basis, or the relationship between linear 
maps and matrices (isomorphism). Let's go with: "A linear map is uniquely 
determined by its values on a basis of the domain."
    *   *Lab Cell (SymPy):* Code to define a matrix representing a linear 
map and apply it.

    *   **Definition**: Start formal. Let $V$ and $W$ be vector spaces 
over a field $\mathbb{F}$. A mapping $T: V \to W$ is called a **linear 
map** (or linear transformation) if it preserves the operations of vector 
addition and scalar multiplication...
        *   Formulae: $T(\mathbf{u} + \mathbf{v}) = T(\mathbf{u}) + 
T(\mathbf{v})$ and $T(c\mathbf{v}) = cT(\mathbf{v})$.

    *   **Worked Example**: Let $\mathbb{R}^2$ be the domain and 
$\mathbb{R}$ be the codomain. Define $T: \mathbb{R}^2 \to \mathbb{R}$ by 
$T(x, y) = 3x - y$.
        *   Show linearity: $(x_1+x_2, y_1+y_2) \mapsto 
3(x_1+x_2)-(y_1+y_2) = (3x_1-y_1)+(3x_2-y_2)$.
        *   Scalar multiplication: $T(c(x,y)) = T(cx, cy) = 3(cx)-cy = 
c(3x-y) = cT(x,y)$.

    *   **Key Theorem**: Let $\mathcal{B} = \{v_1, \dots, v_n\}$ be a 
basis for $V$. If $T: V \to W$ is a linear map, then for any vector 
$\mathbf{v} = \sum c_i v_i$, it follows that $T(\mathbf{v}) = \sum c_i 
T(v_i)$.
        *   Significance: This implies the behavior of $T$ on all points 
in the space is governed by its values on a finite set of basis vectors.

    *   **Lab Cell**: SymPy code to represent this as a matrix 
multiplication.

    *   Check word count (aiming for ~350 words).
    *   Ensure LaTeX formatting.
    *   Check tone: "precise and formal".

    *Refining the Work Example*: Maybe use a transformation of 
polynomials? No, keep it accessible but rigorous for first-year. 
$\mathbb{R}^n$ is standard.

    *Drafting the content:*

    **Definition: Linear Map**
    Let $V$ and $W$ be vector spaces over a field $\mathbb{F}$ (typically 
$\mathbb{R}$ or $\mathbb{C}$). A function $T: V \to W$ is called a 
**linear map** (or linear transformation) if it satisfies the following 
two properties for all vectors $\mathbf{u}, \mathbf{v} \in V$ and all 
scalars $c \in \mathbb{F}$:
    1.  Additivity: $T(\mathbf{u} + \mathbf{v}) = T(\mathbf{u}) + 
T(\mathbf{v})$
    2.  Homogeneity: $T(c\mathbf{v}) = cT(\mathbf{v})$

    These two conditions can be combined into a single requirement: 
$T(c\mathbf{u} + \mathbf{v}) = cT(\mathbf{u}) + T(\mathbf{v})$. A linear 
map preserves the algebraic structure of the vector space, ensuring that 
operations performed before mapping are equivalent to those performed 
after mapping.

    **Worked Example**
    Consider the transformation $T: \mathbb{R}^2 \to \mathbb{R}$ defined 
by $T(x, y) = 5x - 2y$. To verify that $T$ is a linear map, we test both 
conditions. Let $\mathbf{u} = (x_1, y_1)$ and $\mathbf{v} = (x_2, y_2)$.
    \begin{align*}
    T(\mathbf{u} + \mathbf{v}) &= T(x_1+x_2, y_1+y_2) \\
    &= 5(x_1+x_2) - 2(y_1+y_2) \\
    &= (5x_1 - 2y_1) + (5x_2 - 2y_2) = T(\mathbf{u}) + T(\mathbf{v}).
    \end{align*}
    Furthermore, for any scalar $c \in \mathbb{R}$:
    \begin{align*}
    T(c\mathbf{u}) &= T(cx_1, cy_1) \\
    &= 5(cx_1) - 2(cy_1) = c(5x_1 - 2y_1) = cT(\mathbf{u}).
    \end{align*}
    Thus, $T$ is a linear map.

    **Theorem: Basis Determination**
    Let $V$ be a vector space and $\mathcal{B} = \{\mathbf{e}_1, \dots, 
\mathbf{e}_n\}$ be a basis for $V$. Let $T: V \to W$ be a linear map. The 
behavior of $T$ is uniquely determined by its action on the basis vectors. 
Specifically, for any $\mathbf{v} = \sum_{i=1}^n c_i \mathbf{e}_i$, it 
holds that:
    $$T(\mathbf{v}) = T\left(\sum_{i=1}^n c_i \mathbf{e}_i\right) = 
\sum_{i=1}^n c_i T(\mathbf{e}_i)$$
    This result establishes the fundamental link between linear maps and 
matrix representations: if $\mathcal{B}$ is a basis for $V$ and 
$\mathcal{B}'$ is a basis for $W$, then $T$ can be represented as a matrix 
$A$ such that $T(\mathbf{v}) = A\mathbf{[v]}$.

    **Lab Cell (SymPy)**
    ```python
    import sympy as sp

    # Define the domain and codomain dimensions
    # Represent a linear map T: R^2 -> R using a matrix representation
    M = sp.Matrix([[5, -2]])

    # Define input vectors
    u1 = sp.Matrix([1, 2])
    u2 = sp.Matrix([3, 4])

    # Apply the linear map (matrix multiplication)
    v1 = M * u1
    v2 = M * u2

    print(f"T(u1) = {v1}")
    print(f"T(u2) = {v2}")
    ```

    Word count check: ~350 words. Perfect.

    Check constraints:
    - No preamble/metadata? Yes.
    - LaTeX for all math? Yes.
    - Proper structure? Yes.
...done thinking.

### Definition: Linear Map

Let $V$ and $W$ be vector spaces over a field $\mathbb{F}$ (typically 
$\mathbb{R}$ or $\mathbb{C}$). A mapping $T: V \to W$ is defined as a 
**linear map** (or linear transformation) if it preserves the operations 
of vector addition and scalar multiplication. Specifically, $T$ must 
satisfy the following two conditions for all vectors $\mathbf{u}, 
\mathbf{v} \in V$ and all scalars $c \in \mathbb{F}$:

1.  **Additivity**: $T(\mathbf{u} + \mathbf{v}) = T(\mathbf{u}) + 
T(\mathbf{v})$
2.  **Homogeneity**: $T(c\mathbf{v}) = cT(\mathbf{v})$

These properties can be combined into a single requirement: $T(c\mathbf{u} 
+ \mathbf{v}) = cT(\mathbf{u}) + T(\mathbf{v})$. A mapping that fails 
either condition is not linear. Geometrically, in $\mathbb{R}^n$, this 
implies that the image of a line is a line (or a point) and the origin is 
always mapped to the origin: $T(\mathbf{0}_V) = \mathbf{0}_W$.

### Worked Example

Consider a transformation $T: \mathbb{R}^2 \to \mathbb{R}$ defined by the 
rule $T(x, y) = 3x + 4y$. To verify that $T$ is a linear map, we test both 
requirements. Let $\mathbf{u} = (x_1, y_1)$ and $\mathbf{v} = (x_2, y_2)$ 
be elements of $\mathbb{R}^2$, and let $c$ be a scalar.

**Additivity**:
$$T(\mathbf{u} + \mathbf{v}) = T(x_1+x_2, y_1+y_2) = 3(x_1+x_2) + 
4(y_1+y_2)$$
$$= (3x_1 + 4y_1) + (3x_2 + 4y_2) = T(\mathbf{u}) + T(\mathbf{v})$$

**Homogeneity**:
$$T(c\mathbf{u}) = T(cx_1, cy_1) = 3(cx_1) + 4(cy_1)$$
$$= c(3x_1 + 4y_1) = cT(\mathbf{u})$$

Since both conditions hold, $T$ is a linear map.

### Key Theorem: Basis Determination

**Theorem.** Let $V$ be a vector space and $\mathcal{B} = \{\mathbf{e}_1, 
\mathbf{e}_2, \dots, \mathbf{e}_n\}$ be a basis for $V$. Let $T: V \to W$ 
be a linear map. The action of $T$ on any vector $\mathbf{v} \in V$ is 
uniquely determined by its action on the basis vectors. Specifically, if 
$\mathbf{v} = \sum_{i=1}^n c_i \mathbf{e}_i$, then:
$$T(\mathbf{v}) = T\left( \sum_{i=1}^n c_i \mathbf{e}_i \right) = 
\sum_{i=1}^n c_i T(\mathbf{e}_i)$$
This result implies that to define a linear map completely, one only needs 
to specify the images of the basis vectors. This principle provides the 
foundation for representing linear maps as matrices: if $\mathcal{B}$ and 
$\mathcal{B}'$ are bases for $V$ and $W$, there exists a unique matrix $A$ 
such that $T(\mathbf{v}) = A\mathbf{v}$.

### Lab cell (SymPy)
```python
import sympy as sp

# Define the transformation T: R^2 -> R via matrix representation
# The linear map is represented by the matrix M = [[3, 4]]
M = sp.Matrix([[3, 4]])

# Define two input vectors in the domain V = R^2
u1 = sp.Matrix([1, 2])
u2 = sp.Matrix([3, 5])

# Apply the linear map to both vectors
v1 = M * u1
v2 = M * u2

print(f"T(u1) = {v1}")
print(f"T(u2) = {v2}")
```

---

Thinking...
Expert linear algebra author.
Span (within the context of vector spaces).
University textbook.
Precise, formal, full definition, proof sketch, concrete worked example.
First-year university students with calculus background.
300–400 words per section.
Definition $\rightarrow$ Worked Example $\rightarrow$ Key Theorem 
$\rightarrow$ Lab cell (SymPy).
LaTeX for math, no preamble/metadata.

    *   *Concept:* Span of a set of vectors $\{v_1, \dots, v_k\}$.
    *   *Mathematical Definition:* The set of all linear combinations 
$c_1v_1 + \dots + c_kv_k$ where $c_i \in \mathbb{F}$.
    *   *Worked Example:* A simple 2D or 3D example. Let's do a plane in 
$\mathbb{R}^3$.
    *   *Key Theorem:* The span of a set is a subspace (Subspace 
Criterion). Or perhaps something about the dimension/basis relationship? 
"The span of any subset $S \subseteq V$ is the smallest subspace 
containing $S$." Let's go with the property that $\text{span}(S)$ is a 
subspace.
    *   *Lab Cell:* SymPy code to calculate the span (or rather, check if 
a vector is in the span).

    *   *Definition section:* Define Span formally using linear 
combinations. Emphasize it as an operation on a set of vectors.
        *   $\text{span}(\{v_1, \dots, v_k\}) = \{ c_1v_1 + \dots + c_kv_k 
: c_i \in \mathbb{F} \}$.

    *   *Worked Example:* Let $S = \{(1, 0, 1), (0, 1, 1)\}$. Find 
$\text{span}(S)$.
        *   Explain that this results in a plane in $\mathbb{R}^3$.
        *   Show the specific calculation: $(c_1, c_2, c_1+c_2)$.

    *   *Theorem:* The span of any set $S \subseteq V$ is a subspace of 
$V$.
        *   Proof sketch: Closure under addition and scalar 
multiplication.

    *   *Lab Cell (SymPy):* Provide code to check if a vector lies in the 
span of a given matrix/set.

    *   *Refining Length:* Need to hit ~300-400 words total.
    *   *Style Check:* Ensure formal tone ("Let $V$ be a vector 
space...").

    *Drafting the Definition:*
    "Let $V$ be a vector space over a field $\mathbb{F}$. Let $S = \{v_1, 
v_2, \dots, v_k\}$ be a finite subset of $V$. The **span** of $S$, denoted 
$\text{span}(S)$, is the set of all linear combinations of the vectors in 
$S$."
    $\text{span}(S) = \{ c_1v_1 + c_2v_2 + \dots + c_kv_k \mid c_i \in 
\mathbb{F} \}$.

    *Drafting Example:*
    Consider $V = \mathbb{R}^3$ and the set $S = \{v_1, v_2\} = \{(1, 0, 
1), (0, 1, 1)\}$. Any element $x \in \text{span}(S)$ takes the form:
    $x = c_1(1, 0, 1) + c_2(0, 1, 1) = (c_1, c_2, c_1+c_2)$.
    Since $c_1$ and $c_2$ are independent variables, this represents a 
plane in $\mathbb{R}^3$.

    *Drafting Theorem:*
    Theorem: Let $S \subseteq V$. Then $\text{span}(S)$ is a subspace of 
$V$.
    Proof Sketch: (1) The zero vector $\mathbf{0}$ is in the span because 
setting all $c_i=0$ yields $\mathbf{0}$. (2) If $u, v \in \text{span}(S)$, 
they are linear combinations $\sum a_i v_i$ and $\sum b_i v_i$. Their sum 
$u+v = \sum (a_i+b_i)v_i$ is also in the span. (3) Scalar multiplication 
follows similarly.

    *SymPy:*
    ```python
    import sympy as sp
    # Define vectors
    v1 = sp.Matrix([1, 0, 1])
    v2 = sp.Matrix([0, 1, 1])
    # Check if a target vector is in the span
    target = sp.Matrix([1, 1, 2])
    matrix = sp.Matrix([[v1, v2]])
    # Solve for coefficients
    sol = matrix.1.solve_linear_system(target)
    print(f"Coefficients: {sol}")
    ```

    *   Refine language to be "precise and formal". Use "Let $\mathcal{S} 
\subset V$". Mention that the span is the smallest subspace containing 
$\mathcal{S}$.
    *   Check word count.

    (Self-Correction during drafting): Make sure the distinction between a 
set of vectors and their linear combination is clear. Ensure the 
transition from definition to example is smooth.

    Word Count Check:
    Definition ~60 words
    Example ~90 words
    Theorem ~80 words
    Intro/Transitions ~20 words
    Total ~250 + SymPy code. I need a bit more meat in the explanation of 
the theorem to reach 300-400 range comfortably while maintaining "precise" 
style.

    *Expansion:* Elucidate that $\text{span}(S)$ is the set of all points 
reachable via linear combinations, and mention the relationship between 
basis and span (though focus is on span). Explain the subspace criterion 
more thoroughly in the theorem.
...done thinking.

### The Span of a Set of Vectors

**Definition.** Let $V$ be a vector space over a field $\mathbb{F}$, and 
let $S = \{v_1, v_2, \dots, v_k\}$ be a finite subset of vectors in $V$. 
The **span** of $S$, denoted by $\text{span}(S)$, is the set of all 
possible linear combinations of the vectors in $S$:
$$\text{span}(S) = \left\{ \sum_{i=1}^{k} c_i v_i \mid c_i \in \mathbb{F} 
\right\}$$
The span represents the collection of all vectors that can be "reached" by 
scaling and adding the elements of $S$. Geometrically, if $V = 
\mathbb{R}^3$, the span of a single non-zero vector is a line through the 
origin; the span of two non-parallel vectors is a plane passing through 
the origin.

**Worked Example.** Consider the vector space $\mathbb{R}^3$ and the set 
$S = \{v_1, v_2\}$ where:
$$v_1 = \begin{bmatrix} 1 \\ 0 \\ 1 \end{bmatrix}, \quad v_2 = 
\begin{bmatrix} 0 \\ 1 \\ 1 \end{bmatrix}$$
A vector $x$ is in $\text{span}(S)$ if it can be expressed as $x = c_1v_1 
+ c_2v_2$. Substituting the components:
$$x = c_1\begin{bmatrix} 1 \\ 0 \\ 1 \end{bmatrix} + c_2\begin{bmatrix} 0 
\\ 1 \\ 1 \end{bmatrix} = \begin{bmatrix} c_1 \\ c_2 \\ c_1+c_2 
\end{bmatrix}$$
To determine if a specific vector, such as $w = [2, -1, 1]^T$, lies in 
$\text{span}(S)$, we solve for $c_1$ and $c_2$:
$$c_1 = 2, \quad c_2 = -1 \implies c_1 + c_2 = 2 + (-1) = 1$$
Since a consistent solution exists, $w \in \text{span}(S)$.

**Theorem.** Let $V$ be a vector space and $S \subseteq V$. The subspace 
$\text{span}(S)$ is the smallest subspace of $V$ containing $S$.
*Proof Sketch:* To show $\text{span}(S)$ is a subspace, we verify the 
three subspace axioms: 
1. **Additive Identity**: Setting all coefficients $c_i = 0$ yields the 
zero vector $\mathbf{0} \in \text{span}(S)$. 
2. **Closure under Addition**: Let $u, v \in \text{span}(S)$. Then $u = 
\sum a_i v_i$ and $v = \sum b_i v_i$. Their sum is $u+v = \sum (a_i + 
b_i)v_i$, which is a linear combination of elements in $S$.
3. **Closure under Scalar Multiplication**: For any $k \in \mathbb{F}$, 
$ku = k\sum a_i v_i = \sum (ka_i)v_i$, which remains in $\text{span}(S)$.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define vectors in R^3
v1 = sp.Matrix([1, 0, 1])
v2 = sp.Matrix([0, 1, 1])
target_vector = sp.Matrix([2, -1, 1])

# Construct a matrix where columns are the spanning vectors
M = sp.Matrix([[v1, v2]])

# Solve for coefficients c1 and c2 such that M * [c1, c2]^T = 
target_vector
try:
    coeffs = M.solve(target_vector)
    print(f"Target vector in span? Yes. Coefficients: {coeffs}")
except_exception:
    print("Target vector is not in the span.")
```

---

Thinking...
Expert linear algebra author.
University textbook.
Precise, formal.
Full definition, proof sketch (or intuitive derivation/justification), 
concrete worked example.
First-year university student with calculus background.
300-400 words per section.
Definition $\rightarrow$ Worked Example $\rightarrow$ Key Theorem 
$\rightarrow$ Lab Cell (SymPy).
Basis (within the context of "basis").

    *   Need a precise definition of a basis: A set $B = \{v_1, \dots, 
v_n\}$ is a basis for a vector space $V$ if it is linearly independent and 
spans $V$.
    *   Wait, let's refine the components. Definition involves Linear 
Independence and Spanning Set.

    *   *Definition:* Let $V$ be a vector space over a field $\mathbb{F}$. 
A set of vectors $\mathcal{B} = \{v_1, v_2, \dots, v_n\} \subset V$ is 
called a **basis** for $V$ if it satisfies two conditions:
        1.  $\mathcal{B}$ is linearly independent: $\sum_{i=1}^n c_i v_i = 
0 \implies c_i = 0$ for all $i$.
        2.  $\mathcal{B}$ spans $V$: Every vector $v \in V$ can be written 
as $v = \sum_{i=1}^n c_i v_i$ for some scalars $c_i \in \mathbb{F}$.

    *   *Worked Example:* Let $V = \mathbb{R}^3$. Consider the set 
$\mathcal{B} = \{(1, 0, 1), (0, 1, 1), (1, 1, 0)\}$. Show it's a basis.
        *   Linear independence: $c_1(1,0,1) + c_2(0,1,1) + c_3(1,1,0) = 
(0,0,0)$. System of equations: $c_1+c_3=0$, $c_2+c_3=0$, $c_1+c_2=0$. 
Adding all gives $2c_1+2c_2+2c_3=0 \implies c_1+c_2+c_3=0$. Substituting 
$c_1=-c_3$ and $c_2=-c_3$ into $c_1+c_2=0$ gives $-2c_3=0$, so $c_3=0$, 
hence $c_1=0, c_2=0$.
        *   Span: Any $(x,y,z) = a(1,0,1) + b(0,1,1) + c(1,1,0)$ leads to 
$a+c=x$, $b+c=y$, $a+b=z$. Solving gives unique coefficients.

    *   *Key Theorem:* The Uniqueness of Representation Theorem. If 
$\mathcal{B}$ is a basis, every $v \in V$ has a *unique* representation as 
a linear combination of elements in $\mathcal{B}$.
        *   Proof Sketch: Suppose $v = \sum c_i v_i$ and $v = \sum d_i 
v_i$. Then $\sum (c_i - d_i) v_i = 0$. Since $\{v_i\}$ is linearly 
independent, $c_i - d_i = 0$, so $c_i = d_i$.

    *   *Lab Cell:* SymPy code to check if a set of vectors forms a basis 
for $\mathbb{R}^3$.

    *   Word count target: 300-400 words.
    *   Language level: Formal/Precise.
    *   Math: LaTeX.

    *Drafting the content:*

    **Definition: Basis**
    Let $V$ be a vector space over a field $\mathbb{F}$. A set of vectors 
$\mathcal{B} = \{v_1, v_2, \dots, v_n\} \subset V$ is called a **basis** 
for $V$ if it satisfies the following two conditions:
    1. $\mathcal{B}$ is linearly independent: The only scalars $c_1, c_2, 
\dots, c_n \in \mathbb{F}$ such that $\sum_{i=1}^n c_i v_i = \mathbf{0}$ 
are $c_1 = c_2 = \dots = c_n = 0$.
    2. $\mathcal{B}$ spans $V$: For every vector $v \in V$, there exist 
scalars $a_1, a_2, \dots, a_n \in \mathbb{F}$ such that $v = \sum_{i=1}^n 
a_i v_i$.
    A basis provides a minimal generating set for the space; every vector 
can be uniquely identified by its coordinates relative to $\mathcal{B}$.

    *Example:*
    Consider $V = \mathbb{R}^3$ and the set $\mathcal{B} = \{(1, 0, 1), 
(0, 1, 1), (1, 1, 0)\}$. To verify $\mathcal{B}$ is a basis, we check 
linear independence. Suppose $c_1(1, 0, 1) + c_2(0, 1, 1) + c_3(1, 1, 0) = 
(0, 0, 0)$. This leads to the system:
    $c_1 + c_3 = 0$, $c_2 + c_3 = 0$, and $c_1 + c_2 = 0$.
    Subtracting the second from the first gives $c_1 - c_2 = 0 \implies 
c_1 = c_2$. Substituting into $c_1+c_2=0$ yields $2c_1=0$, so $c_1=0$, 
which implies $c_2=0$ and $c_3=0$. Since only the trivial solution exists, 
$\mathcal{B}$ is linearly independent. Because $|\mathcal{B}| = 
\dim(\mathbb{R}^3) = 3$, it automatically spans the space and thus 
constitutes a basis.

    *Theorem: Uniqueness of Representation.*
    If $\mathcal{B} = \{v_1, \dots, v_n\}$ is a basis for $V$, then every 
vector $v \in V$ can be expressed as a linear combination of elements in 
$\mathcal{B}$ in exactly one way.
    *Proof Sketch:* Suppose $v = \sum_{i=1}^n c_i v_i$ and $v = 
\sum_{i=1}^n d_i v_i$. Then $\sum (c_i - d_i) v_i = 0$. By the definition 
of linear independence, $c_i - d_i = 0$ for all $i$, hence $c_i = d_i$.

    *Lab Cell:*
    (Need SymPy code).

    Current word count check:
    Def: ~60 words.
    Ex: ~130 words.
    Thm: ~70 words.
    Lab: ~50-ish content.
    Total $\approx$ 310-350. Good.

    *Refining the "Theory" part:* I should ensure it's clear that a basis 
implies both span and independence.

    Let's double check the constraints.
    - Precise/Formal: Yes.
    - Full definition, proof sketch, example: Yes.
    - 300-400 words: Yes.
    - SymPy cell included.
...done thinking.

### Basis

**Definition.** Let $V$ be a vector space over a field $\mathbb{F}$. A set 
of vectors $\mathcal{B} = \{v_1, v_2, \dots, v_n\} \subset V$ is called a 
**basis** for $V$ if it satisfies the following two conditions:
1.  **Linear Independence**: The only scalars $c_1, c_2, \dots, c_n \in 
\mathbb{F}$ such that $\sum_{i=1}^n c_i v_i = \mathbf{0}$ are $c_1 = c_2 = 
\dots = c_n = 0$.
2.  **Spanning**: Every vector $v \in V$ can be expressed as a linear 
combination of the vectors in $\mathcal{B}$. That is, for any $v \in V$, 
there exist scalars $a_1, a_2, \dots, a_n \in \mathbb{F}$ such that $v = 
\sum_{i=1}^n a_i v_i$.

A basis serves as a coordinate system for the vector space; it is a 
"minimal" generating set in the sense that removing any element would 
result in a set that no longer spans $V$.

**Worked Example.** Consider the vector space $\mathbb{R}^3$ and the set 
$\mathcal{B} = \{(1, 0, 1), (0, 1, 1), (1, 1, 0)\}$. To prove 
$\mathcal{B}$ is a basis, we check linear independence by setting a linear 
combination equal to the zero vector:
$$c_1(1, 0, 1) + c_2(0, 1, 1) + c_3(1, 1, 0) = (0, 0, 0)$$
This yields the system of equations:
$$\begin{cases} c_1 + c_3 = 0 \\ c_2 + c_3 = 0 \\ c_1 + c_2 = 0 
\end{cases}$$
From $c_1+c_3=0$ and $c_2+c_3=0$, we get $c_1 = -c_3$ and $c_2 = -c_3$. 
Substituting into the third equation gives $-c_3 - c_3 = 0 \implies c_3 = 
0$, which forces $c_1=0$ and $c_2=0$. Since only the trivial solution 
exists, $\mathcal{B}$ is linearly independent. Because $\mathcal{B}$ 
contains 3 vectors and $\dim(\mathbb{R}^3) = 3$, it spans $\mathbb{R}^3$ 
and is thus a basis.

**Theorem (Uniqueness of Representation).** If $\mathcal{B} = \{v_1, 
\dots, v_n\}$ is a basis for $V$, then every vector $v \in V$ can be 
uniquely expressed as a linear combination of the elements of 
$\mathcal{B}$.
*Proof Sketch:* Suppose $v$ has two representations: $v = \sum c_i v_i$ 
and $v = \sum d_i v_i$. Subtracting these equations yields $\sum (c_i - 
d_i) v_i = \mathbf{0}$. By the linear independence of $\mathcal{B}$, it 
must follow that $c_i - d_i = 0$ for all $i$, implying $c_i = d_i$.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define a set of vectors in R^3
# Vector 1: (1, 0, 1), Vector 2: (0, 1, 1), Vector 3: (1, 1, 0)
M = sp.Matrix([[1, 0, 1], 
                [0, 1, 1], 
                [1, 1, 0]])

# A set of vectors forms a basis if the matrix they form is non-singular
is_basis = M.det() != 0
print(f"Determinant: {M.det()}")
print(f"Is it a basis? {is_basis}")
```

---

Thinking...
Expert linear algebra author.
Norm (linear algebra).
University textbook.
Precise and formal tone, full definition/proof sketch/worked example.
First-year university student with calculus background.
300–400 words per section.
Definition $\rightarrow$ Worked Example $\rightarrow$ Key Theorem 
$\rightarrow$ Lab Cell (SymPy).
$\LaTeX$ for all math.

    *   **Section 1: Definition.** Define what a norm is mathematically 
($||\cdot||$). List the three axioms: non-negativity/separability, 
homogeneity, and triangle inequality. Explain the physical intuition 
(magnitude of a vector).
    *   **Section 2: Worked Example.** Calculate the Euclidean norm 
($\ell^2$-norm) for a specific vector in $\mathbb{R}^n$ and perhaps 
mention the Manhattan norm or $L^\infty$ norm briefly to show variety. 
Let's stick to the Euclidean norm for clarity in the calculation.
    *   **Section 3: Key Theorem.** The equivalence of norms on 
finite-dimensional spaces is a powerful result. Alternatively, the 
relationship between the norm and the inner product (induced norm) is very 
important for first-year students. I will choose the *Equivalence of 
Norms* theorem as it's fundamental to analysis/linear algebra foundations.
    *   **Section 4: Lab Cell.** SymPy code to calculate the $L^p$ norm 
and illustrate the difference between $\ell_1, \ell_2,$ and $\ell_\infty$.

    *   *Introduction:* Define a norm as a function mapping a vector space 
to the non-negative reals.
    *   *Axioms:*
        1. $\|x\| = 0 \iff x = \mathbf{0}$
        2. $\|\alpha x\| = |\alpha| \|x\|$ (Absolute homogeneity)
        3. $\|x + y\| \le \|x\| + \|y\|$ (Triangle inequality)

    *   *Worked Example:* Let $v = [3, 4] \in \mathbb{R}^2$. Calculate 
$\|v\|_2$. $\sqrt{3^2 + 4^2} = 5$. Also mention $\|v\|_1 = |3| + |4| = 7$.

    *   *Theorem:* Equivalence of Norms. If $V$ is finite-dimensional, all 
norms are equivalent (i.e., there exist constants $C_1, C_2 > 0$ such that 
$C_1 \|x\|_a \le \|x\|_b \le C_2 \|x\|_a$).

    *   *Word Count Check:* Need to ensure it hits the 300-400 word range. 
I'll need to expand on the geometric intuition and properties of the 
triangle inequality slightly.

    *   *Drafting - Definition Section*:
        "A norm is a function $\mathcal{N}: V \to \mathbb{R}$ that assigns 
a non-negative length to every vector in a vector space $V$..." (Expand on 
axioms).

    *   *Drafting - Worked Example:* Provide clear calculations for 
Euclidean and Taxicab norms.

    *   *Drafting - Theorem*: "Theorem: Equivalence of Norms." Explain 
that while they measure size differently, they define the same topology in 
finite dimensions.

    *   *Drafting - Lab Cell:* Use SymPy's `norm` or just manual 
calculation to show $L_p$ norms. Let's use a custom function for clarity 
across different types.

    *   "precisely and formal": Check.
    *   "full definition, proof sketch, concrete worked example": 
Included.
    *   "300-400 words": Need to be careful here. The total 
section (Definition + Example + Theorem + Lab) needs to hit the target.

    *(Self-Correction during drafting)*: If the *total* section must be 
300-400, I need to keep it concise but dense.

    *Refining Definition:*
    A norm is a mapping $\|\cdot\| : V \to \mathbb{R}$ on a vector space 
$V$ over $\mathbb{R}$ or $\mathbb{C}$ that quantifies the magnitude of 
vectors. For $\| \cdot \|$ to qualify as a norm, it must satisfy the 
following three axioms for all $x, y \in V$ and scalars $\alpha$:
    1. **Separability**: $\|x\| = 0$ if and only if $x = \mathbf{0}$.
    2. **Absolute Homogeneity**: $\|\alpha x\| = |\alpha| \|x\|$.
    3. **Triangle Inequality**: $\|x + y\| \leq \|x\| + \|y\|$.

    *Refining Example:* Let $\mathbf{v} = (3, 4) \in \mathbb{R}^2$. Under 
the Euclidean norm $\|\cdot\|_2$, we have $\|\mathbf{v}\|_2 = \sqrt{3^2 + 
4^2} = 5$. Under the $L^1$ norm $\|x\|_1 = \sum |x_i|$, we have 
$\|\mathbf{v}\|_1 = 7$.

    *Refining Theorem:* Equivalence of Norms.
    "Theorem: Let $V$ be a finite-dimensional vector space over 
$\mathbb{R}$. Any two norms $\|\cdot\|_a$ and $\|\cdot\|_b$ on $V$ are 
equivalent; that is, there exist constants $c_1, c_2 > 0$ such that $c_1 
\|x\|_a \leq \|x\|_b \leq c_2 \|x\|_a$ for all $x \in V$."
    *Proof Sketch:* Since any norm on a finite-dimensional space is 
bounded by the maximum of its components multiplied by a constant, and 
there are only finitely many basis vectors, we can construct bounding 
constants.

    *Word Count Check:*
    Intro/Def: ~80 words.
    Example: ~60 words.
    Theorem: ~100 words.
    Lab: (Not counted in prose word count usually, but the whole block 
needs to feel substantial). Total should be around 350.

    *Refining Content*: Make sure it's "precise and formal." Use 
$\mathbb{R}$ notation correctly. Ensure SymPy code is clean.
...done thinking.

### Norms

**Definition.** Let $V$ be a vector space over the field $\mathbb{R}$ (or 
$\mathbb{C}$). A **norm** on $V$ is a function $\|\cdot\|: V \to 
\mathbb{R}$ that assigns a real number to every vector $x \in V$, 
representing its magnitude. To qualify as a norm, the mapping must satisfy 
the following three axioms for all vectors $x, y \in V$ and any scalar 
$\alpha$:

1.  **Separability**: $\|x\| = 0$ if and only if $x = \mathbf{0}$.
2.  **Absolute Homogeneity**: $\|\alpha x\| = |\alpha| \|x\|$.
3.  **Triangle Inequality**: $\|x + y\| \leq \|x\| + \|y\|$.

Common examples include the Euclidean norm ($\ell^2$-norm), defined as 
$\|x\|_2 = \sqrt{\sum |x_i|^2}$, and the Manhattan norm ($\ell^1$-norm), 
defined as $\|x\|_1 = \sum |x_i|$.

**Worked Example.** Consider a vector $v = \begin{bmatrix} 3 \\ 4 
\end{bmatrix}$ in $\mathbb{R}^2$. We calculate its magnitude under two 
different norms:
1.  **$\ell^2$-norm**: $\|v\|_2 = \sqrt{3^2 + 4^2} = \sqrt{9+16} = 5$.
2.  **$\ell^1$-norm**: $\|v\|_1 = |3| + |4| = 7$.
While both values provide a measure of "size," the $\ell^2$-norm 
corresponds to the standard geometric distance from the origin, whereas 
the $\ell^1$-norm represents the sum of absolute displacements.

**Theorem (Equivalence of Norms).** Let $V$ be a finite-dimensional vector 
space. Any two norms $\|\cdot\|_a$ and $\|\cdot\|_b$ on $V$ are 
**equivalent**. That is, there exist constants $c_1, c_2 > 0$ such that 
for all $x \in V$:
$$c_1 \|x\|_a \leq \|x\|_b \leq c_2 \|x\|_a$$
*Proof Sketch:* Since any norm on a finite-dimensional space is bounded by 
a multiple of the maximum component of the vector (the $\ell^\infty$ 
norm), and all such "maximum" norms are related to one another via 
constants, it follows that any two norms must be bounded by each other.

**Lab Cell (SymPy)**
```python
import sympy as sp

def calculate_norms(vector, p_value):
    """Calculates the L^p norm for a given vector."""
    # Define the vector components
    x = sp.Matrix([3, 4])
    # Calculate Lp norm: (sum(|x_i|^p))^(1/p)
    lp_norm = (sum(abs(x[i])**p_value))**(1/p_value)
    return sp.simplify(lp_norm)

# Example usages
print(f"L2 Norm: {calculate_norms(None, 2)}") # Expected: 5
print(f"L1 Norm: {calculate_norms(None, 1)}") # Expected: 7
```

---

Thinking...
*   Role: Expert linear algebra author.
    *   Style Guide: University textbook (precise, formal).
    *   Depth: Full definition, proof sketch, concrete worked example.
    *   Audience: First-year university student with calculus background.
    *   Length: 300–400 words per section.
    *   Structure: Definition $\rightarrow$ Worked Example $\rightarrow$ 
Key Theorem $\rightarrow$ Lab Cell (SymPy).
    *   Subject: Orthogonality (within the context of "orthogonality").

    *   *Concept:* Orthogonality in an inner product space.
    *   *Key terms:* Inner product, orthogonal vectors, dot product (as a 
specific case), Pythagorean theorem for orthogonal vectors.
    *   *Structure specifics:*
        1.  Definition: Formal definition of orthogonality via the inner 
product $\langle \mathbf{u}, \mathbf{v} \rangle = 0$.
        2.  Worked Example: Calculating orthogonality in $\mathbb{R}^n$ 
and a function space (to show breadth). Let's stick to vectors first or 
perhaps a mix.
        3.  Key Theorem: The Pythagorean Theorem for orthogonal vectors 
($\|\mathbf{u} + \mathbf{v}\|^2 = \|\mathbf{u}\|^2 + \|\mathbf{v}\|^2$).
        4.  Lab Cell (SymPy): Code showing the dot product and checking 
orthogonality condition.

    *   *Definition:* Start with an inner product space $(V, \langle 
\cdot, \cdot \rangle)$. Define two vectors $\mathbf{u}, \mathbf{v} \in V$ 
as orthogonal if $\langle \mathbf{u}, \mathbf{v} \rangle = 0$. Mention the 
geometric interpretation (perpendicularity).
    *   *Example:* Take $\mathbf{u} = (1, 2, -1)$ and $\mathbf{v} = (2, 
-1, 3)$ in $\mathbb{R}^3$. No, wait. Let's make them actually orthogonal 
for a "worked example" or show how to check it. $(1, 2, 1)$ and $(2, -1, 
-2) \rightarrow 2-2-2 \neq 0$. Let's use $\mathbf{u} = (1, 1)$ and 
$\mathbf{v} = (1, -1)$. $1(1) + 1(-1) = 0$. Simple.
    *   *Theorem:* Pythagorean Theorem. Statement: If $\mathbf{u} \perp 
\mathbf{v}$, then $\|\mathbf{u} + \mathbf{v}\|^2 = \|\mathbf{u}\|^2 + 
\|\mathbf{v}\|^2$. Provide a brief sketch: Expand the norm squared as 
$\langle \mathbf{u}+\mathbf{v}, \mathbf{u}+\mathbf{v} \rangle$ and use 
linearity.
    *   *SymPy:* Show `sympy.Matrix` dot product or similar.

    *   *Constraint Check:* 300-400 words per section. The prompt says 
"section" (singular), but the content encompasses the whole structure for 
one concept ("orthogonality"). I need to ensure the total length of this 
block is between 300 and 400 words.

    *   *Drafting Content:*
        Definition: Let $V$ be a vector space over $\mathbb{R}$ equipped 
with an inner product $\langle \cdot, \cdot \rangle$. Two vectors 
$\mathbf{u}, \mathbf{v} \in V$ are said to be *orthogonal*, denoted by 
$\mathbf{u} \perp \mathbf{v}$, if and only if their inner product is zero: 
$\langle \mathbf{u}, \mathbf{v} \rangle = 0$. In the Euclidean space 
$\mathbb{R}^n$, where the standard dot product is used, this condition 
corresponds to geometric perpendicularity.

        Worked Example: Consider vectors $\mathbf{u} = (2, 3)$ and 
$\mathbf{v} = (3, -2)$ in $\mathbb{R}^2$ equipped with the standard dot 
product $\mathbf{u} \cdot \mathbf{v}$. To determine if they are 
orthogonal, we compute:
        $\langle \mathbf{u}, \mathbf{v} \rangle = (2)(3) + (3)(-2) = 6 - 6 
= 0$.
        Since the inner product is zero, $\mathbf{u}$ and $\mathbf{v}$ are 
orthogonal.

        Theorem: Pythagorean Theorem for Orthogonal Vectors. Let $V$ be an 
inner product space. If $\mathbf{u}, \mathbf{v} \in V$ are such that 
$\mathbf{u} \perp \mathbf{v}$, then $\|\mathbf{u} + \mathbf{v}\|^2 = 
\|\mathbf{u}\|^2 + \|\mathbf{v}\|^2$.
        Proof Sketch: By the properties of the inner product, we expand 
the norm squared:
        $\|\mathbf{u} + \mathbf{v}\|^2 = \langle \mathbf{u} + \mathbf{v}, 
\mathbf{u} + \mathbf{v} \rangle$
        $= \langle \mathbf{u}, \mathbf{u} \rangle + \langle \mathbf{u}, 
\mathbf{v} \rangle + \langle \mathbf{v}, \mathbf{u} \rangle + \langle 
\mathbf{v}, \mathbf{v} \rangle$.
        If $\mathbf{u} \perp \mathbf{v}$, then $\langle \mathbf{u}, 
\mathbf{v} \rangle = 0$ and $\langle \mathbf{v}, \mathbf{u} \rangle = 0$, 
yielding $\|\mathbf{u}\|^2 + \|\mathbf{v}\|^2$.

        Lab Cell:
        ```python
        import sympy
        u = sympy.Matrix([2, 3])
        v = sympy.Matrix([3, -2])
        is_orthogonal = u.dot(v) == 0
        print(f"Dot Product: {u.dot(v)}")
        print(f"Orthogonal: {is_orthogonal}")
        ```

    *   Word count check:
        Intro/Def: ~50 words
        Example: ~50 words
        Theorem/Proof: ~80 words
        Lab Cell info/setup: ~30 words.
        Total is around 210 words currently. I need to expand the text 
slightly to meet the 300-400 range without sacrificing the formal tone.

    *   *Expansion Strategy:* Elaborate on the geometric interpretation of 
orthogonality and the definition of the norm in terms of the inner 
product. Explain why $\langle \mathbf{v}, \mathbf{u} \rangle$ also 
vanishes (symmetry).

    *   *Refined Draft Construction:*
        (Def) Define Orthogonality: Let $(V, \langle \cdot, \cdot 
\rangle)$ be an inner product space over the field $\mathbb{R}$. Two 
vectors $\mathbf{x}, \mathbf{y} \in V$ are said to be *orthogonal*, 
denoted as $\mathbf{x} \perp \mathbf{y}$, if their inner product 
satisfies:
        $$\langle \mathbf{x}, \mathbf{y} \rangle = 0$$
        In the specific case of $\mathbb{R}^n$ equipped with the standard 
Euclidean inner product (the dot product), orthogonality implies that the 
vectors are geometrically perpendicular. This concept provides a 
foundational framework for defining projections and constructing 
orthonormal bases in higher-dimensional spaces.

        (Example) Consider the vectors $\mathbf{u} = \begin{bmatrix} 1 \\ 
2 \\ -3 \end{bmatrix}$ and $\mathbf{v} = \begin{bmatrix} 2 \\ 3 \\ 1 
\end{bmatrix}$ in $\mathbb{R}^3$. To determine if these vectors are 
orthogonal under the standard inner product, we compute:
        $$\langle \mathbf{u}, \mathbf{v} \rangle = (1)(2) + (2)(3) + 
(-3)(1) = 2 + 6 - 3 = 5$$
        Since $\langle \mathbf{u}, \mathbf{v} \rangle \neq 0$, these 
vectors are not orthogonal. However, if we take $\mathbf{w} = 
\begin{bmatrix} 3 \\ -1 & \end{bmatrix}$ and $\mathbf{z} = \begin{bmatrix} 
1 & 2 \end{bmatrix}$, then:
        $$\langle \mathbf{w}, \mathbf{z} \rangle = (3)(1) + (-1)(2) = 1 
\neq 0$$
        Wait, let's make a definite one. Let $\mathbf{u} = [1, 1]$ and 
$\mathbf{v} = [1, -1]$.
        $\langle \mathbf{u}, \mathbf{v} \rangle = (1)(1) + (1)(-1) = 0$. 
Here, $\mathbf{u} \perp \mathbf{v}$.

        (Theorem) Pythagorean Theorem. Let $V$ be an inner product space 
and let $\mathbf{x}, \mathbf{y} \in V$. If $\mathbf{x} \perp \mathbf{y}$, 
then:
        $$\|\mathbf{x} + \mathbf{y}\|^2 = \|\mathbf{x}\|^2 + 
\|\mathbf{y}\|^2$$
        *Proof Sketch:* By the definition of the induced norm 
$\|\mathbf{v}\| = \sqrt{\langle \mathbf{v}, \mathbf{v} \rangle}$, we 
expand the following:
        $$\|\mathbf{x} + \mathbf{y}\|^2 = \langle \mathbf{x} + \mathbf{y}, 
\mathbf{x} + \mathbf{y} \rangle$$
        Applying the linearity of the inner product in both slots, we 
obtain:
        $$\langle \mathbf{x}, \mathbf{x} \rangle + \langle \mathbf{x}, 
\mathbf{y} \rangle + \langle \mathbf{y}, \mathbf{x} \rangle + \langle 
\mathbf{y}, \mathbf{y} \rangle$$
        By the symmetry property of real inner products, $\langle 
\mathbf{x}, \mathbf{y} \rangle = \langle \mathbf{y}, \mathbf{x} \rangle$. 
Since orthogonality implies $\langle \mathbf{x}, \mathbf{y} \rangle = 0$, 
the middle terms vanish, leaving:
        $$\|\mathbf{x}\|^2 + \|\mathbf{y}\|^2$$

    *   Word Count Check of Refined Draft: ~315 words. Perfect.

    Check constraints one last time:
    - Style: Precise and formal (Yes).
    - Depth: Full definition, proof sketch, worked example (Yes).
    - Audience: First-year students (Yes).
    - Length: 300-400 words (Yes).
    - Structure: Def -> Example -> Theorem -> Lab Cell.

    Wait, the prompt asks for "No preamble, no metadata." and specifically 
to output only the section text. I will ensure the SymPy cell is properly 
formatted as a block.
...done thinking.

### Orthogonality

**Definition.** Let $(V, \langle \cdot, \cdot \rangle)$ be an inner 
product space over the field $\mathbb{R}$. Two vectors $\mathbf{x}, 
\mathbf{y} \in V$ are said to be *orthogonal*, denoted by $\mathbf{x} 
\perp \mathbf{y}$, if and only if their inner product is zero:
$$\langle \mathbf{x}, \mathbf{y} \rangle = 0$$
In the Euclidean space $\mathbb{R}^n$ equipped with the standard dot 
product, this condition corresponds to geometric perpendicularity. 
Orthogonality is a fundamental property used to decompose vectors into 
independent components and to construct orthonormal bases, where every 
basis vector has unit length and is orthogonal to all others in the set.

**Worked Example.** Consider the vector space $\mathbb{R}^3$ with the 
standard inner product. We wish to determine if the following vectors are 
orthogonal:
$$\mathbf{u} = \begin{bmatrix} 2 \\ -1 \\ 4 \end{bmatrix}, \quad 
\mathbf{v} = \begin{bmatrix} 2 \\ 1 \\ -1 \end{bmatrix}$$
To check for orthogonality, we compute the dot product:
$$\langle \mathbf{u}, \mathbf{v} \rangle = (2)(2) + (-1)(1) + (4)(-1) = 4 
- 1 - 4 = -1$$
Since $\langle \mathbf{u}, \mathbf{v} \rangle \neq 0$, the vectors 
$\mathbf{u}$ and $\mathbf{v}$ are not orthogonal. Conversely, if we take 
$\mathbf{w} = \begin{bmatrix} 1 \\ 2 \end{bmatrix}$ and $\mathbf{z} = 
\begin{bmatrix} -2 \\ 1 \end{bmatrix}$, then:
$$\langle \mathbf{w}, \mathbf{z} \rangle = (1)(-2) + (2)(1) = -2 + 2 = 0$$
Thus, $\mathbf{w} \perp \mathbf{z}$.

**Theorem.** *Pythagorean Theorem for Orthogonal Vectors.* Let $V$ be an 
inner product space. If $\mathbf{x}, \mathbf{y} \in V$ are orthogonal such 
that $\mathbf{x} \perp \mathbf{y}$, then:
$$\|\mathbf{x} + \mathbf{y}\|^2 = \|\mathbf{x}\|^2 + \|\mathbf{y}\|^2$$
*Proof Sketch:* By the definition of the norm induced by an inner product, 
$\|\mathbf{v}\|^2 = \langle \mathbf{v}, \mathbf{v} \rangle$. Expanding the 
sum:
$$\|\mathbf{x} + \mathbf{y}\|^2 = \langle \mathbf{x} + \mathbf{y}, 
\mathbf{x} + \mathbf{y} \rangle$$
By the linearity and symmetry of the inner product:
$$\|\mathbf{x} + \mathbf{y}\|^2 = \langle \mathbf{x}, \mathbf{x} \rangle + 
\langle \mathbf{x}, \mathbf{y} \rangle + \langle \mathbf{y}, \mathbf{x} 
\rangle + \langle \mathbf{y}, \mathbf{y} \rangle$$
Since $\mathbf{x} \perp \mathbf{y}$ implies $\langle \mathbf{x}, 
\mathbf{y} \rangle = 0$ and $\langle \mathbf{y}, \mathbf{x} \rangle = 0$, 
the expression simplifies to:
$$\|\mathbf{x}\|^2 + \|\mathbf{y}\|^2$$

**Lab Cell (SymPy)**
```python
import sympy

# Define vectors in R^3
u = sympy.Matrix([2, -1, 4])
v = sympy.Matrix([2, 1, -1])
w = sympy.Matrix([1, 2])
z = sympy.Matrix([-2, 1])

# Check orthogonality using the dot product
print(f"u . v = {u.dot(v)}")           # Should be non-zero
print(f"w . z = {w.dot(z)}")           # Should be zero (orthogonal)

# Verify Pythagorean Theorem: ||w + z||^2 == ||w||^2 + ||z||^2
sum_norm_sq = (w + z).norm()**2
individual_norms_sq = w.norm()**2 + z.norm()**2
print(f"Pythagorean holds: {sum_norm_sq == individual_norms_sq}")
```

---

Thinking...
Expert linear algebra author.
Adjoint (of a linear operator/matrix).
University textbook.
Precise, formal.
Full definition, proof sketch, concrete worked example, SymPy lab cell.
First-year university student with calculus background.
300-400 words per section.
Definition $\rightarrow$ Worked example $\rightarrow$ Key theorem 
$\rightarrow$ Lab cell (SymPy).
$\LaTeX$ for math. Output only the text.

    *   Define adjoint in the context of an inner product space $V$.
    *   Distinguish between the "adjoint" as a linear operator $T^*$ and 
the conjugate transpose $(\mathbf{A}^*)$ if it's a matrix representation, 
but usually, in advanced linear algebra, the operator definition is 
primary. Let's stick to the operator definition ($ \langle Tv, w \rangle = 
\langle v, T^*w \rangle $) as it is more general.
    *   Clarify real vs. complex cases (Hermitian adjoint).

    *   *Definition:* Start with a finite-dimensional inner product space 
$V$ over $\mathbb{F} \in \{\mathbb{R}, \mathbb{C}\}$. Let $T: V \to V$ be 
a linear operator. The adjoint $T^*$ is the unique operator such that 
$\langle Tv, w \rangle = \langle v, T^*w \rangle$ for all $v, w \in V$. If 
$\mathbb{F} = \mathbb{R}$, it's the transpose in matrix form; if 
$\mathbb{C}$, it's conjugate transpose.
    *   *Worked Example:* Let $V = \mathbb{C}^2$ with the standard dot 
product. Define a matrix $A = \begin{pmatrix} 1 & i \\ 2 & 3 
\end{pmatrix}$. Find its adjoint (conjugate transpose). Calculate $\langle 
Av, w \rangle$.
    *   *Key Theorem:* The relationship between eigenvalues and 
eigenvectors of $T$ vs $T^*$, or the property $(AB)^* = B^*A^*$. Let's go 
with the $(AB)^* = B^*A^*$ as it highlights the "reversal" property which 
is central to linear algebra. Or perhaps something about self-adjoint 
operators? Let's stick to $(AB)^* = B^*A^*$.
    *   *Lab Cell:* Python code using `sympy` to compute the conjugate 
transpose of a matrix.

    *   *Section: The Adjoint Operator.*
    *   Definition block: Define inner product space $V$, operator $T \in 
\mathcal{L}(V)$, and the unique $T^*$. Note the uniqueness comes from the 
Riesz Representation Theorem (briefly implied).
    *   Worked Example: Use a 2D complex vector space. $A = 
\begin{pmatrix} 1 & i \\ -i & 4 \end{pmatrix}$. Wait, let's make it 
non-Hermitian to show difference. Let $M = \begin{pmatrix} 1 & 2+i \\ 3 & 
0 \end{pmatrix}$.
    *   Theorem: $\langle Tv, w \rangle = \langle v, T^*w \rangle$. Show 
$(T_1 T_2)^* = T_2^* T_1^*$.
    *   SymPy Code: `Matrix([[1, 2+1j], [3, 0]]).H`.

    *   *Self-correction on Word Count:* Need to hit 300-400 words. Let's 
expand the definitions slightly and ensure the theorem proof sketch is 
clear.
    *   Structure Check: Definition $\rightarrow$ Worked example 
$\rightarrow$ Key theorem $\rightarrow$ Lab cell.

    *   *Drafting Definitions:* Start with "Let $V$ be an inner product 
space..." Define the adjoint $T^*$. Emphasize that in the case of a matrix 
representation $A$, $A^* = \overline{A}^T$.
    *   *Worked Example:* Let's use $\mathbb{C}^2$. $v, w \in 
\mathbb{C}^2$. $M = \begin{pmatrix} 1 & i \\ 2 & 3 \end{pmatrix}$. 
Calculate $M^*$. Show that $\langle Mv, w \rangle$ is indeed equal to 
$\langle v, M^*w \rangle$.
    *   *Theorem:* State $(AB)^* = B^* A^*$. Provide a brief proof sketch 
using the definition.

    *   Check LaTeX: use `$...$` for inline and `\begin{equation}` or `\[ 
... \]` for blocks. (Standard practice is usually just block if it's big).
    *   SymPy: Ensure standard syntax for conjugate transpose `.H`.
...done thinking.

### The Adjoint Operator

**Definition.** Let $V$ be a finite-dimensional inner product space over 
the field $\mathbb{F}$ (where $\mathbb{F} = \mathbb{R}$ or $\mathbb{C}$). 
For any linear operator $T: V \to V$, the **adjoint** of $T$ is the unique 
linear operator $T^*: V \to V$ that satisfies the following identity for 
all vectors $v, w \in V$:
$$\langle Tv, w \rangle = \langle v, T^*w \rangle$$
In the specific case where $V = \mathbb{R}^n$ or $\mathbb{C}^n$ and $T$ is 
represented by a matrix $A$, the adjoint $T^*$ corresponds to the 
conjugate transpose (or Hermitian transpose) of the matrix. That is, if 
$T$ is represented by $A$, then $T^*$ is represented by $A^* = 
\overline{A}^T$.

**Worked Example.** Consider the complex inner product space 
$\mathbb{C}^2$ with the standard inner product $\langle \mathbf{v}, 
\mathbf{w} \rangle = \sum v_i \bar{w}_i$. Let $T$ be the linear operator 
represented by the matrix:
$$A = \begin{pmatrix} 1 & i \\ 2 & 3 \end{pmatrix}$$
To find the adjoint $T^*$, we calculate the conjugate transpose of $A$:
$$A^* = \overline{\begin{pmatrix} 1 & i \\ 2 & 3 \end{pmatrix}}^T = 
\begin{pmatrix} 1 & -i \\ 2 & 3 \end{pmatrix}^T = \begin{pmatrix} 1 & 2 \\ 
-i & 3 \end{pmatrix}$$
Verification: Let $\mathbf{v} = \begin{pmatrix} v_1 \\ v_2 \end{pmatrix}$ 
and $\mathbf{w} = \begin{pmatrix} w_1 \\ w_2 \end{pmatrix}$. The inner 
product $\langle A\mathbf{v}, \mathbf{w} \rangle$ is:
$$\left\langle \begin{pmatrix} v_1 + iv_2 \\ 2v_1 + 3v_2 \end{pmatrix}, 
\begin{pmatrix} w_1 \\ w_2 \end{pmatrix} \right\rangle = (v_1 + 
iv_2)\bar{w}_1 + (2v_1 + 3v_2)\bar{w}_2$$
The inner product $\langle \mathbf{v}, A^*\mathbf{w} \rangle$ is:
$$\left\langle \begin{pmatrix} v_1 \\ v_2 \end{pmatrix}, \begin{pmatrix} 
w_1 + 2w_2 \\ -iw_1 + 3w_2 \end{pmatrix} \right\rangle = v_1(\bar{w}_1 + 
2\bar{w}_2) + v_2(i\bar{w}_1 + 3\bar{w}_2) = v_1\bar{w}_1 + 2v_1\bar{w}_2 
+ iv_2\bar{w}_1 + 3v_2\bar{w}_2$$
Both expressions are algebraically identical, confirming $A^* = 
\begin{pmatrix} 1 & 2 \\ -i & 3 \end{pmatrix}$.

**Theorem.** Let $T$ and $S$ be linear operators on a finite-dimensional 
inner product space $V$. The adjoint of the composition follows the 
reverse-order property:
$$(TS)^* = S^* T^*$$
*Proof Sketch:* By the definition of the adjoint, $\langle (TS)v, w 
\rangle = \langle S(Tv), w \rangle$. Applying the definition to the 
operator $S$, we have $\langle S(Tv), w \rangle = \langle Tv, T^*w 
\rangle$. Finally, applying the definition to the operator $T$ regarding 
the vector $T^*w$, we obtain $\langle v, T^*(T^*w) \rangle = \langle v, 
(T^*T^*)w \rangle$? No, strictly: $\langle Sv, w\rangle = \langle v, S^*w 
\rangle$. Thus, $\langle T(Sv), w \rangle = \langle Sv, T^*w \rangle = 
\langle v, S^*(T^*w) \rangle$. By the uniqueness of the adjoint, $(TS)^* = 
S^* T^*$.

**Lab cell (SymPy)**
```python
import sympy as sp

# Define a complex matrix representing operator T
A = sp.Matrix([[1, sp.I], [2, 3]])

# The .H property in SymPy computes the conjugate transpose (adjoint)
A_adj = A.H

print(f"Original Matrix A:\n{A}")
print(f"Adjoint Matrix A*:\n{A_adj}")

# Verify the property: <Av, w> == <v, A*w>
v = sp.Matrix([sp.Symbol('v1'), sp.Symbol('v2')])
w = sp.Matrix([sp.Symbol('w1'), sp.Symbol('w2')])

left_side = A * v * w._conjugate() # Using a simplified dot product 
representation
right_side = v * w.conjugate() # This requires proper inner product 
mapping in SymPy
# More precisely, using the internal conjugate transpose:
def inner_product(vec1, vec2):
    return sum(vec1[i] * sp.conjugate(vec2[i]) for i in range(len(vec1)))

print(f"Inner product check: {inner_product(A*v, w) == inner_product(v, 
A_adj*w)}")
```

---

Thinking...
Expert linear algebra author.
Eigenpair (eigenvalue/eigenvector pair).
University textbook.
Precise, formal, 300-400 words per section.

        *   Definition.
        *   Worked example.
        *   Key theorem.
        *   Lab cell (SymPy).
First-year university student with calculus background.
$\LaTeX$ for math.
Only the section text, no preamble/metadata.

    *   Definition: A scalar $\lambda$ and a non-zero vector $\mathbf{v}$ 
such that $A\mathbf{v} = \lambda\mathbf{v}$. Explain components 
(eigenvalue vs. eigenvector).
    *   Worked example: Pick a 2x2 matrix, e.g., $A = \begin{pmatrix} 4 & 
1 \\ 2 & 3 \end{pmatrix}$ or something similar that's easy to calculate 
but not trivial. Let's use $\begin{pmatrix} 3 & 1 \\ 1 & 3 \end{pmatrix}$ 
or $\begin{pmatrix} 5 & 2 \\ 2 & 1 \end{pmatrix}$. Let's go with $A = 
\begin{bmatrix} 4 & 2 \\ 1 & 3 \end{bmatrix}$.
    *   Key Theorem: The Characteristic Equation $(\det(A - \lambda I) = 
0)$.
    *   Lab Cell: SymPy code to find eigenvalues/eigenvectors.

    *   *Section Title:* **Eigenpairs** (or just the content).
    *   *Definition:* An eigenpair consists of a scalar $\lambda$ and a 
non-zero vector $\mathbf{v}$ satisfying $A\mathbf{v} = \lambda\mathbf{v}$. 
Define "eigenvalue" and "eigenvector". Mention that $\mathbf{v} \neq 
\mathbf{0}$ is crucial.
    *   *Worked Example:* Let $A = \begin{pmatrix} 4 & 2 \\ 1 & 3 
\end{pmatrix}$. Find the eigenpairs. Step-by-step: $(\lambda - 4)(\lambda 
- 3) - 2 = 0 \Rightarrow \lambda^2 - 7\lambda + 12 - 2 = 0$ (Wait, let's 
make it cleaner). Let $A = \begin{pmatrix} 1 & 2 \\ 2 & 1 \end{pmatrix}$. 
$\det(A-\lambda I) = (1-\lambda)^2 - 4 = 0 \Rightarrow 1-\lambda = \pm 2 
\Rightarrow \lambda_1=3, \lambda_2=-1$.
    *   *Key Theorem:* Characteristic Equation. State that the eigenvalues 
are roots of $p(\lambda) = \det(A - \lambda I)$. Proof sketch: If 
$A\mathbf{v} = \lambda\mathbf{v}$, then $(A-\lambda I)\mathbf{v} = 
\mathbf{0}$. For non-zero $\mathbf{v}$ to exist, the matrix must be 
singular.
    *   *Lab Cell:* SymPy `eigenvalues` and `eigenvectors`.

    *   Check word count: Aiming for 300-400 words total. (Actually, the 
prompt says "per section", but there's only one concept requested). I need 
to ensure each block is substantial enough to meet the depth requirement 
while staying within the limit.
    *   Tone check: Precise and formal.

    *Refining Content:*
    Definition: Use $\mathbf{v} \in \mathbb{V}$ (usually $\mathbb{R}^n$ or 
$\mathbb{C}^n$).
    Worked Example: $A = \begin{bmatrix} 3 & 1 \\ 1 & 3 \end{bmatrix}$. 
Characteristic equation $(3-\lambda)^2 - 1 = 0 \Rightarrow (3-\lambda) = 
\pm 1$. $\lambda_1=4, \lambda_2=2$.
    Eigenvectors: For $\lambda=4$, $x+y=4-3x \dots$ No. $(A-\lambda 
I)\mathbf{v} = 0$.
    For $\lambda=4$: $\begin{pmatrix} -1 & 1 \\ 1 & -1 
\end{pmatrix}\begin{pmatrix} x \\ y \end{pmatrix} = \begin{pmatrix} 0 \\ 0 
\end{pmatrix} \Rightarrow x=y$. $\mathbf{v}_1 = [1, 1]^T$.
    For $\lambda=2$: $\begin{pmatrix} 1 & 1 \\ 1 & 1 
\end{pmatrix}\begin{pmatrix} x \\ y \end{pmatrix} = \begin{pmatrix} 0 \\ 0 
\end{pmatrix} \Rightarrow x=-y$. $\mathbf{v}_2 = [1, -1]^T$.

    *Word count check:*
    Intro/Def: ~60 words.
    Example: ~100 words.
    Theorem: ~80 words.
    Lab Cell: ~30 words (code usually doesn't count much toward "word" 
limits in the same way prose does, but I will keep it concise).

    *Wait, total word count 300-400.* I need to expand a bit on the 
explanation of why $\mathbf{v} \neq \mathbf{0}$ is required and the 
significance of the characteristic equation.

    *Refined Draft:*
    "Definition: Let $A$ be an $n \times n$ matrix over a field 
$\mathbb{F}$. An **eigenpair** $(\lambda, \mathbf{v})$ consists of a 
scalar $\lambda \in \mathbb{F}$ and a non-zero vector $\mathbf{v} \in 
\mathbb{F}^n$ such that:
    $$A\mathbf{v} = \lambda\mathbf{v}$$
    In this context, $\lambda$ is called an **eigenvalue** of $A$, and 
$\mathbf{v}$ is the corresponding **eigenvector**. The existence of a 
non-zero vector is necessary because the equation $A\mathbf{0} = 
\lambda\mathbf{0}$ is satisfied for any $\lambda$, providing no 
information about the linear transformation's properties."

    "Worked Example: Consider the matrix $A = \begin{pmatrix} 3 & 1 \\ 1 & 
3 \end{pmatrix}$. We seek pairs $(\lambda, \mathbf{v})$ such that 
$A\mathbf{v} = \lambda\mathbf{v}$.
    Substituting into the characteristic equation $(3-\lambda)^2 - 1 = 0$, 
we find $\lambda_1 = 4$ and $\lambda_2 = 2$.
    For $\lambda_1 = 4$:
    $$\begin{pmatrix} 3-4 & 1 \\ 1 & 3-4 \end{pmatrix} \begin{pmatrix} x 
\\ y \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix} \Rightarrow -x + 
y = 0$$
    The eigenspace is spanned by $\mathbf{v}_1 = \begin{pmatrix} 1 \\ 1 
\end{pmatrix}$. For $\lambda_2 = 2$:
    $$\begin{pmatrix} 3-2 & 1 \\ 1 & 3-2 \end{pmatrix} \begin{pmatrix} x 
\\ y \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix} \Rightarrow x + 
y = 0$$
    The eigenspace is spanned by $\mathbf{v}_2 = \begin{pmatrix} 1 \\ -1 
\end{pmatrix}$."

    "Theorem: The Characteristic Equation. Let $A$ be an $n \times n$ 
matrix. A scalar $\lambda$ is an eigenvalue of $A$ if and only if the 
characteristic polynomial $p(\lambda) = \det(A - \lambda I)$ equals zero.
    *Proof Sketch:* The equation $A\mathbf{v} = \lambda\mathbf{v}$ can be 
rewritten as $(A - \lambda I)\mathbf{v} = \mathbf{0}$. For a non-zero 
vector $\mathbf{v}$ to exist, the matrix $(A - \lambda I)$ must be 
singular (non-invertible). By the properties of determinants, this occurs 
if and only if $\det(A - \lambda I) = 0$."

    "Lab Cell: [SymPy Code]"

    Total words approx: ~250. Need to expand slightly on 
theory/explanation to hit 300-400 range safely while maintaining "precise" 
tone.

    *Addition:* Add a sentence about the geometric interpretation (scaling 
along a direction). Explain that eigenvectors define directions where the 
linear transformation acts only by scaling.

    Final check:
    Definition? Yes.
    Worked example? Yes.
    Theorem? Yes.
    Lab cell? Yes.
    LaTeX? Yes.
    No preamble? Yes.
...done thinking.

### Eigenpairs

**Definition.** Let $A \in \mathbb{F}^{n \times n}$ be a square matrix 
over a field $\mathbb{F}$. An **eigenpair** is a tuple $(\lambda, 
\mathbf{v})$ consisting of a scalar $\lambda \in \mathbb{F}$ and a 
non-zero vector $\mathbf{v} \in \mathbb{F}^n$ such that:
$$A\mathbf{v} = \lambda\mathbf{v}$$
In this context, the scalar $\lambda$ is referred to as an **eigenvalue** 
of $A$, and the vector $\mathbf{v}$ is the corresponding **eigenvector**. 
Geometrically, an eigenvector represents a direction in the vector space 
that remains invariant under the linear transformation $A$, except for a 
scaling factor of $\lambda$. It is critical that $\mathbf{v} \neq 
\mathbf{0}$, as the trivial solution $\mathbf{v}=\mathbf{0}$ does not 
provide information regarding the transformation's properties.

**Worked Example.** Consider the matrix $A = \begin{pmatrix} 3 & 1 \\ 1 & 
3 \end{pmatrix}$. We seek the eigenpairs $(\lambda, \mathbf{v})$ for this 
system. To find $\lambda$, we solve the characteristic equation:
$$\det(A - \lambda I) = (3-\lambda)^2 - 1 = 0$$
This yields $(3-\lambda)^2 = 1$, giving eigenvalues $\lambda_1 = 4$ and 
$\lambda_2 = 2$.

For $\lambda_1 = 4$, we find the associated eigenvector:
$$\begin{pmatrix} 3-4 & 1 \\ 1 & 3-4 \end{pmatrix} \begin{pmatrix} x \\ y 
\end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix} \implies -x + y = 0$$
Choosing $x=1$ gives $\mathbf{v}_1 = \begin{pmatrix} 1 \\ 1 
\end{pmatrix}$. For $\lambda_2 = 2$:
$$\begin{pmatrix} 3-2 & 1 \\ 1 & 3-2 \end{pmatrix} \begin{pmatrix} x \\ y 
\end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix} \implies x + y = 0$$
Choosing $x=1$ gives $\mathbf{v}_2 = \begin{pmatrix} 1 \\ -1 
\end{pmatrix}$. The eigenpairs are $(4, [1, 1]^T)$ and $(2, [1, -1]^T)$.

**Key Theorem.** *The Characteristic Equation.* Let $A \in \mathbb{F}^{n 
\times n}$. A scalar $\lambda$ is an eigenvalue of $A$ if and only if it 
is a root of the characteristic polynomial $p(\lambda) = \det(A - \lambda 
I)$.

*Proof Sketch:* The defining equation $A\mathbf{v} = \lambda\mathbf{v}$ 
can be rearranged as $(A - \lambda I)\mathbf{v} = \mathbf{0}$. For a 
non-zero vector $\mathbf{v}$ to exist, the matrix $(A - \lambda I)$ must 
be singular. From the fundamental properties of linear algebra, a square 
matrix is singular if and only if its determinant is zero. Thus, we 
require $\det(A - \lambda I) = 0$.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define the matrix A
A = sp.Matrix([[3, 1], [1, 3]])

# Calculate eigenvalues and eigenvectors
eigen_pairs = A.eigenvects()

for i, (val, vec) in enumerate(eigen_pairs):
    print(f"Eigenvalue: {val}, Eigenvector: {vec}")
```

---

Thinking...
*   Role: Expert linear algebra author.
    *   Style: University textbook (precise, formal).
    *   Target Audience: First-year university student with calculus 
background.
    *   Content: `orthonormal_basis`.
    *   Structure Requirements: Definition $\rightarrow$ Worked Example 
$\rightarrow$ Key Theorem $\rightarrow$ Lab cell (SymPy).
    *   Length Constraint: 300-400 words per section.
    *   Formatting: LaTeX for all math, no preamble/metadata.

    *   Definition of Orthogonal Basis.
    *   Definition of Orthonormal Basis (orthogonal + unit norm).
    *   Explanation of the inner product's role in determining 
orthogonality and norm.
    *   Why it matters (simplifies projections, coordinates, etc.).

    *   Need a simple vector space ($\mathbb{R}^3$).
    *   Take a set of vectors that are orthogonal but not unit length, 
then normalize them. Or just start with a basis and apply Gram-Schmidt to 
get an orthonormal one? No, keep it simple: verify if a given set is 
orthonormal.
    *   Example: $v_1 = (1, 0, 0)$, $v_2 = (0, \frac{1}{\sqrt{2}}, 0)$, 
$v_3 = (0, 0, \frac{\sqrt{3}}{2})$. Wait, that's not right. They should be 
unit length.
    *   Better: Show the transition from an orthogonal basis to an 
orthonormal one. Let $\{u_1, u_2\} = \{(\sqrt{2}, \sqrt{2}), (0, 2)\}$. 
No, let's keep it simple for a first-year student. Give two vectors $v_1 = 
[1, 1]$ and $v_2 = [-1, 1]$. They are orthogonal but not orthonormal. 
Normalize them.

    *   Gram-Schmidt Process (standard theorem/method to find an ONB).
    *   Or the "Uniqueness of Coordinates" or property that a matrix $Q$ 
with orthonormal columns has $Q^T Q = I$. Let's go with the Gram-Schmidt 
construction as it's the standard path to establishing an ONB.

    *   Python/SymPy code to check orthonormality.

    *   *Section: Orthonormal Basis.*
    *   *Definition:* A set of vectors $\{v_1, \dots, v_k\}$ in a vector 
space $V$ equipped with an inner product $\langle \cdot, \cdot \rangle$ is 
called **orthogonal** if $\langle v_i, v_j \rangle = 0$ for all $i \neq 
j$. It is **orthonormal** if it is orthogonal and each vector has unit 
norm, i.e., $\|v_i\| = \sqrt{\langle v_i, v_i \rangle} = 1$ for all $i=1, 
\dots, k$. Thus, a set $\mathcal{B}$ is orthonormal if $\langle v_i, v_j 
\rangle = \delta_{ij}$, where $\delta$ is the Kronecker delta.
    *   *Worked Example:* Consider $\mathbb{R}^2$ with the standard dot 
product. Let $u_1 = (1, 1)$ and $u_2 = (-1, 1)$.
        1. Check orthogonality: $u_1 \cdot u_2 = (1)(-1) + (1)(1) = 0$. 
They are orthogonal.
        2. Calculate norms: $\|u_1\| = \sqrt{1^2 + 1^2} = \sqrt{2}$, and 
$\|u_2\| = \sqrt{(-1)^2 + 1^2} = \sqrt{2}$.
        3. Construct orthonormal basis: $v_1 = \frac{u_1}{\|u_1\|} = 
(\frac{1}{\sqrt{2}}, \frac{1}{\sqrt{2}})$ and $v_2 = \frac{u_2}{\|u_2\|} = 
(-\frac{1}{\sqrt{2}}, \frac{1}{\sqrt{2}})$.
        The set $\{v_1, v_2\}$ is an orthonormal basis for $\mathbb{R}^2$.
    *   *Theorem:* Gram-Schmidt Process. Let $\{x_1, \dots, x_n\}$ be a 
basis for $V$. Then there exists an orthonormal basis $\{e_1, \dots, 
e_n\}$ such that $\text{span}\{x_1, \dots, x_k\} = \text{span}\{e_1, 
\dots, e_k\}$ for all $k \leq n$.
    *   *Lab Cell:* SymPy code.

    *   Word count check: The text needs to be 300-400 words. I need to 
expand the definitions and explanations slightly to ensure it hits the 
target while maintaining a formal tone.

    *Refining content for length/depth:*
    The definition should mention that an orthonormal basis simplifies 
coordinate calculations because $x = \sum \langle x, e_i \rangle e_i$.
    The theorem section will briefly explain the Gram-Schmidt construction 
logic.

    *   "Precise and formal" -> Use terms like "inner product space," 
"Kronecker delta."
    *   "SymPy cell" inclusion.
...done thinking.

### Orthonormal Basis

**Definition.** Let $V$ be a vector space equipped with an inner product 
$\langle \cdot, \cdot \rangle$. A set of vectors $\{v_1, v_2, \dots, v_n\} 
\subset V$ is said to be **orthogonal** if $\langle v_i, v_j \rangle = 0$ 
for all $i \neq j$. Such a set is called an **orthonormal basis** (ONB) if 
it is orthogonal and each vector possesses unit norm, such that $\|v_i\| = 
\sqrt{\langle v_i, v_i \rangle} = 1$ for all $i \in \{1, \dots, n\}$. 
Formally, a set $\mathcal{B}$ is an orthonormal basis if:
$$\langle v_i, v_j \rangle = \delta_{ij}$$
where $\delta_{ij}$ is the Kronecker delta ($\delta_{ij} = 1$ if $i=j$, 
and $0$ otherwise). An orthonormal basis provides a particularly 
convenient coordinate system; for any vector $x \in V$, its coordinates 
relative to an ONB are simply given by the projections: $x = \sum_{i=1}^n 
\langle x, v_i \rangle v_i$.

**Worked Example.** Consider the vector space $\mathbb{R}^2$ equipped with 
the standard Euclidean inner product (dot product). We are given a basis 
$\{u_1, u_2\}$ where $u_1 = \begin{pmatrix} 1 \\ 1 \end{pmatrix}$ and $u_2 
= \begin{pmatrix} -1 \\ 1 \end{pmatrix}$. To determine if this is an 
orthonormal basis:
1.  **Check Orthogonality:** $\langle u_1, u_2 \rangle = (1)(-1) + (1)(1) 
= 0$. The vectors are orthogonal.
2.  **Check Norms:** $\|u_1\| = \sqrt{1^2 + 1^2} = \sqrt{2}$ and $\|u_2\| 
= \sqrt{(-1)^2 + 1^2} = \sqrt{2}$.
Since the norms are not equal to $1$, $\{u_1, u_2\}$ is an orthogonal 
basis but not an orthonormal one. To construct an orthonormal basis 
$\mathcal{B} = \{v_1, v_2\}$, we normalize each vector:
$$v_1 = \frac{u_1}{\|u_1\|} = \begin{pmatrix} 1/\sqrt{2} \\ 1/\sqrt{2} 
\end{pmatrix}, \quad v_2 = \frac{u_2}{\|u_2\|} = \begin{pmatrix} 
-1/\sqrt{2} \\ 1/\sqrt{2} \end{pmatrix}$$
The set $\{v_1, v_2\}$ is now an orthonormal basis for $\mathbb{R}^2$.

**Theorem (Gram-Schmidt Process).** Let $\{x_1, x_2, \dots, x_n\}$ be a 
basis for an inner product space $V$. There exists an orthonormal basis 
$\{e_1, e_2, \dots, e_n\}$ for $V$ obtained by the following recursive 
construction:
$$u_k = x_k - \sum_{j=1}^{k-1} \text{proj}_{u_j}(x_k), \quad e_k = 
\frac{u_k}{\|u_k\|}$$
This process ensures that each $e_k$ is orthogonal to all preceding 
vectors and has unit length, effectively "straightening" and scaling a 
generic basis into an orthonormal one.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define the vector space and vectors
v1 = sp.Matrix([1, 1])
v2 = sp.Matrix([-1, 1])

# Calculate norms to check orthonormality
norm_v1 = v1.norm()
norm_v2 = v2.norm()

# Normalize the vectors
e1 = v1 / norm_v1
e2 = v2 / norm_v2

print(f"Normalized v1: {e1}")
print(f"Normalized v2: {e2}")

# Verify orthonormality (Inner products should be 1 for i=j and 0 for 
i!=j)
print(f"Inner product e1.e2: {e1.dot(e2)}")
print(f"Norm of e1: {e1.norm()}")
```

---

## Payoff

Thinking...
Expert author of a linear algebra concept-book.
"Payoff" section (the final synthesis/conclusion).
Spectral Theorem, `quantum_observable`, `fourier_modes`.

        *   Tone: Precise and formal.
        *   Depth: Full definition (of the theorem), proof sketch, 
concrete worked example.
        *   Audience: First-year uni students with calculus background.
        *   Length: 300–400 words per section.
        *   Structure: Definition $\rightarrow$ Worked Example 
$\rightarrow$ Key Theorem $\rightarrow$ Lab Cell (SymPy).

    *   *Spectral Theorem:* Diagonalizability of symmetric/Hermitian 
matrices. Transition from general linear transformations to those with 
orthogonal bases of eigenvectors.
    *   *Quantum Observable:* In quantum mechanics, observables are 
represented by Hermitian operators (matrices). The spectral theorem 
ensures real eigenvalues and an orthonormal basis, allowing for a 
well-defined set of measurable states.
    *   *Fourier Modes:* Functions in $L^2$ spaces can be decomposed into 
eigenfunctions of the Laplacian operator. This is essentially the spectral 
theorem applied to differential operators on specific domains.

    *   **Section: The Spectral Theorem.** (The Synthesis)
        *   *Intro/Definition*: Define the Spectral Theorem for symmetric 
matrices (real case) or Hermitian matrices (complex case).
        *   *Worked Example:* Show a $2 \times 2$ symmetric matrix being 
diagonalized.
        *   *Key Theorem Connection to Applications:* Bridge the gap 
between abstract linear algebra and the physical/analytical realms of 
quantum mechanics and signal processing.
        *   *Lab Cell*: Provide SymPy code for eigen-decomposition.

    *   *Drafting Definition:* "The Spectral Theorem provides the ultimate 
synthesis of our study..." Wait, need to follow structure: Definition 
$\rightarrow$ Worked Example $\rightarrow$ Key Theorem $\rightarrow$ Lab 
cell.
    *   *Wait*, looking at the prompt's instruction: "Write a 'Payoff' 
section that: 1. Explains what spectral_theorem achieves... 2. Shows how 
it connects to each listed application... 3. Ends with an invitation..."
    *   *Constraint Check:* The structure in the STYLE GUIDE is 
"Definition $\rightarrow$ Worked example $\rightarrow$ Key theorem 
$\rightarrow$ Lab cell". I must merge these requirements.

    *   *Content Construction:*
        1.  **Definition:** Define the Spectral Theorem (Real 
Symmetric/Complex Hermitian). It states that if $A$ is symmetric, there 
exists an orthogonal matrix $P$ such that $A = PDP^T$.
        2.  **Worked Example:** A simple $2 \times 2$ symmetric matrix $A 
= \begin{pmatrix} 3 & 1 \\ 1 & 3 \end{pmatrix}$. Show eigenvalues 
$\lambda_1=4, \lambda_2=2$.
        3.  **Key Theorem (The Bridge):** Connect to "quantum_observable" 
and "fourier_modes". Explain how the orthogonality of eigenvectors is 
crucial for physical measurement (quantization) and signal decomposition 
(orthogonality).
        4.  **Lab Cell:** SymPy code using `sympy.Matrix` and `.eigh()`.

    *   *Word Count Check:* Aiming for 300-400 words total for the whole 
segment? Or per section? The prompt says "300–400 words per section". 
There's only one section requested ("Payoff"). So I have ~400 words.

    *   *Refining Tone:* Formal, academic. Use $\mathbb{R}$, $\mathbb{C}$.

    *   *Wait, let me double-check the content of "Payoff":*
        1. What it achieves/why it's the endpoint: Transition from 
arbitrary matrices to "nice" ones (symmetric/Hermitain). The ability to 
decompose space into independent components.
        2. Connection to applications: Quantum observables $\implies$ 
Hermiticity ensures real measurements; Fourier Modes $\implies$ 
Eigenfunctions of differential operators provide a basis for signal 
decomposition.

    *   Structure check:
        Definition: Spectral Theorem (Mathematical statement)
        Worked Example: $A = \begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix}$ 
or similar.
        Key Theorem/Link: Connecting the dots to Physics and Engineering.
        Lab Cell: SymPy implementation of `eigh`.

    *   *Wait, "Theorem" in the structure might refer to the logic 
connecting it to applications.*

    *   Let's refine the flow:
        1. **Definition:** The Spectral Theorem for Symmetric Matrices. 
State that $A$ is orthogonally diagonalizable if and only if $A=A^T$.
        2. **Worked Example:** $\mathbf{A} = \begin{bmatrix} 2 & 1 \\ 1 & 
2 \end{bmatrix}$. Eigenvalues are $3, 1$. Eigenvectors are $(1,1)$ and 
$(1,-1)$.
        3. **The Synthesis (Key Theorem):** Explain the "Payoff". In 
quantum mechanics, observables correspond to Hermitian matrices; the 
Spectral Theorem guarantees real eigenvalues (measurable quantities) and 
an orthonormal basis of states. In signal processing, Fourier modes 
represent the projection onto orthogonal eigenfunctions, allowing for 
efficient decomposition of complex signals into fundamental frequencies.
        4. **Lab Cell:** SymPy code using `eigh`.

    *   *Word count check:* Currently around 300-350 words. Perfect.

    Make sure to use LaTeX for all math. Ensure the "Key Theorem" section 
explicitly references 'quantum_observable' and 'fourier_modes'.

    *Self-Correction during drafting:*
    The prompt asks: "Write a 'Payoff' section that... [then lists 3 
points]". I should weave those 3 requirements into the requested structure 
(Def -> Ex $\rightarrow$ Theorem $\rightarrow$ Lab).

    Definition of Spectral Theorem.
    Worked example.
    Synthesis/Key Link to Applications.
    SymPy Cell.

    *Let's tighten the wording for "Expert" quality.* Use terms like 
"orthonormal basis," "Hermitian operator," and "decoupled modes."
...done thinking.

### The Spectral Theorem: The Synthesis of Linear Algebra

**Definition.** Let $A \in \mathbb{R}^{n \times n}$ be a symmetric matrix 
(where $A = A^T$). The **Spectral Theorem** states that there exists an 
orthogonal matrix $P$ ($P^T P = I$) and a diagonal matrix $D$ such that:
$$A = PDP^T$$
Equivalently, the theorem asserts that if $A$ is symmetric, it possesses 
$n$ real eigenvalues (counting multiplicity) and its eigenvectors can be 
chosen to form an orthonormal basis for $\mathbb{R}^n$. This represents 
the ultimate refinement of the eigenvalue problem: while not all matrices 
are diagonalizable, all symmetric matrices are *orthogonally* 
diagonalizable. This property ensures that the transformation preserves 
lengths and angles, decomposing the linear operator into independent, 
decoupled components along orthogonal axes.

**Worked Example.** Consider the symmetric matrix $A = \begin{bmatrix} 3 & 
1 \\ 1 & 3 \end{bmatrix}$.
To find its eigenvalues, we solve $\det(A - \lambda I) = (3-\lambda)^2 - 1 
= 0$, yielding $\lambda_1 = 4$ and $\lambda_2 = 2$. For $\lambda_1 = 4$, 
the eigenvector is $v_1 = [1, 1]^T$; for $\lambda_2 = 2$, it is $v_2 = [1, 
-1]^T$. Normalizing these gives the orthonormal basis:
$$q_1 = \frac{1}{\sqrt{2}}\begin{bmatrix} 1 \\ 1 \end{bmatrix}, \quad q_2 
= \frac{1}{\sqrt{2}}\begin{bmatrix} 1 \\ -1 \end{bmatrix}$$
Thus, $A$ can be expressed as $PDP^T$, where $P = 
\frac{1}{\sqrt{2}}\begin{bmatrix} 1 & 1 \\ 1 & -1 \end{bmatrix}$ and $D = 
\begin{bmatrix} 4 & 0 \\ 0 & 2 \end{bmatrix}$.

**Key Theorem.** The Spectral Theorem serves as the bridge between 
abstract linear algebra and physical reality. In the domain of 
**quantum_observable**, it guarantees that any observable physical 
quantity is represented by a Hermitian matrix; the theorem ensures that 
these measurements yield real numbers (eigenvalues) and that state vectors 
can be decomposed into an orthonormal basis of definite states. In the 
realm of **fourier_modes**, the theorem justifies the decomposition of 
complex signals. By treating differential operators as large, symmetric 
matrices, we decompose signal space into orthogonal "modes," where each 
mode evolves independently.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define a symmetric matrix
A = sp.Matrix([[3, 1], [1, 3]])

# Compute eigenvalues and eigenvectors
# eigh is specifically optimized for symmetric/Hermitian matrices
eigen_vals, eigen_vecs = A.eigh()

print(f"Eigenvalues: {eigen_vals}")
print(f"Orthonormal Eigenvectors: {eigen_vecs}")

# Verify diagonalization: P * D * P^T
P = eigen_vecs
D = sp.diag(eigen_vals)
print(f"Verification (A = PDP^T): {P * D * P.T}")
``` 

*To conclude this journey, you are invited to explore the 
"quantum_observable" module to see how these orthogonal bases allow us to 
calculate probabilities in quantum states.*