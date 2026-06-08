

---

### Section 3.2: Scalar Multiplication

**Definition.** Let $V$ be a vector space over a field $\mathbb{F}$ (where $\mathbb{F}$ is typically $\mathbb{R}$ or $\mathbb{C}$). Scalar multiplication is a mapping $\cdot : \mathbb{F} \times V \to V$ that associates each scalar $\alpha \in \mathbb{F}$ and every vector $\mathbf{v} \in V$ with an element $\alpha\mathbf{v} \in V$. For the standard vector space $\mathbb{R}^n$, a scalar $\alpha \in \mathbb{R}$ multiplies every component of the vector:
$$\alpha(x_1, x_2, \dots, x_n) = (\alpha x_1, \alpha x_2, \dots, \alpha x_n)$$
In more general spaces, such as the space of functions $\mathcal{F}(\mathbb{R}, \mathbb{R})$, scalar multiplication is defined pointwise: $(\alpha f)(x) = \alpha \cdot f(x)$.

**Worked Example.** Consider a vector $\mathbf{v} = \begin{bmatrix} 3 \\ -2 \end{bmatrix}$ in the space $\mathbb{R}^2$ and a scalar $\alpha = \frac{1}{2}$. The product is:
$$\alpha\mathbf{v} = \frac{1}{2} \begin{bmatrix} 3 \\ -2 \end{bmatrix} = \begin{bmatrix} 3/2 \\ -1 \end{bmatrix}$$
In the space of polynomials $\mathbb{P}_n$, let $p(x) = 4x^2 + 2x$ and $\alpha = 3$. The scaled polynomial is:
$$\alpha p(x) = 3(4x^2 + 2x) = 12x^2 + 6x$$

**Theorem (Properties of Scalar Multiplication).** Let $\mathbf{u}, \mathbf{v} \in V$ and $\alpha, \beta \in \mathbb{F}$. The operation of scalar multiplication satisfies the following axioms:
1. $\alpha(\mathbf{u} + \mathbf{v}) = \alpha\mathbf{u} + \alpha\mathbf{v}$ (Distributivity over vector addition)
2. $(\alpha + \beta)\mathbf{v} = \alpha\mathbf{v} + \beta\mathbf{v}$ (Distributivity over scalar addition)
3. $\alpha(\beta\mathbf{v}) = (\alpha\beta)\mathbf{v}$ (Compatibility of operations)
4. $1\mathbf{v} = \mathbf{v}$ (Identity element of the field)

*Proof Sketch:* These properties follow directly from the definitions of addition and multiplication in $\mathbb{R}^n$. For instance, for any component $x_i$ of vector $\mathbf{v}$, $(\alpha + \beta)x_i = \alpha x_i + \beta x_i$ by the distributive law of real numbers.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define a vector in R^2
v = sp.Matrix([3, -2])
# Define a scalar
alpha = sp.Rational(1, 2)

# Perform scalar multiplication
result = alpha * v

print(f"Original Vector: {v}")
print(f"Scalar: {alpha}")
print(f"Result: {result}")

# Example with SymPy's Polynomial class
x = sp.Symbol('x')
p = 4*x**2 + 2*x
scale_factor = 3
print(f"Scaled Polynomial: {scale_factor * p}")
```

---

### Vector Addition

**Definition.** Let $\mathbf{u}, \mathbf{v} \in \mathbb{R}^n$ be vectors in an $n$-dimensional Euclidean space. Each vector is represented as a tuple of its components: $\mathbf{u} = (u_1, u_2, \dots, u_n)$ and $\mathbf{v} = (v_1, v_2, \dots, v_n)$. The sum $\mathbf{w} = \mathbf{u} + \mathbf{v}$ is defined by the component-wise addition of their respective entries:
$$\mathbf{w} = \mathbf{u} + \mathbf{v} = (u_1 + v_1, u_2 + v_2, \dots, u_n + v_n)$$
Geometrically, in $\mathbb{R}^2$ or $\mathbb{R}^3$, vector addition corresponds to the "triangle law" or "parallelogram law," where the resultant vector $\mathbf{w}$ is the diagonal of a parallelogram formed by $\mathbf{u}$ and $\mathbf{v}$.

**Worked Example.** Consider vectors from $\mathbb{R}^3$ representing displacements in three-dimensional space. Let:
$$\mathbf{u} = \begin{bmatrix} 2 \\ -1 \\ 4 \end{bmatrix}, \quad \mathbf{v} = \begin{bmatrix} 3 \\ 5 \\ -2 \end{bmatrix}$$
To find the resultant vector $\mathbf{w} = \mathbf{u} + \mathbf{v}$, we perform addition component-wise:
$$\mathbf{w} = \begin{bmatrix} 2+3 \\ -1+5 \\ 4+(-2) \end{bmatrix} = \begin{bmatrix} 5 \\ 4 \\ 2 \end{bmatrix}$$

**Theorem.** Let $\mathbf{u}, \mathbf{v}, \mathbf{w} \in \mathbb{R}^n$. Vector addition satisfies the following properties:
1. **Commutativity:** $\mathbf{u} + \mathbf{v} = \mathbf{v} + \mathbf{u}$.
2. **Associativity:** $(\mathbf{u} + \mathbf{v}) + \mathbf{w} = \mathbf{u} + (\mathbf{v} + \mathbf{w})$.
3. **Identity:** There exists a zero vector $\mathbf{0} = (0, 0, \dots, 0)$ such that $\mathbf{u} + \mathbf{0} = \mathbf{u}$.

*Proof Sketch:* Since the addition of vectors in $\mathbb{R}^n$ is defined by addition in the field $\mathbb{R}$ for each component $i \in \{1, \dots, n\}$, the properties of vector addition are inherited directly from the arithmetic properties of real numbers. For example, because $u_i + v_i = v_i + u_i$ for all $i$, it follows that $\mathbf{u} + \mathbf{v} = \mathbf{v} + \mathbf{u}$.

**Lab Cell (SymPy)**
```python
import sympy as sp

def vector_add(v1, v2):
    """Performs component-wise addition of two vectors."""
    return [x + y for x, y in zip(v1, v2)]

# Define two vectors in R^3
u = [sp.Symbol('u1'), sp.Symbol('u2'), sp.Symbol('u3')]
v = [sp.Symbol('v1'), sp.Symbol('v2'), sp.Symbol('v3')]

# Example with numerical values
u_num = [2, -1, 4]
v_num = [3, 5, -2]

result = vector_add(u_num, v_num)
print(f"The sum of {u_num} and {v_num} is: {result}")
```

---

### Linear Combination

**Definition**
Let $V$ be a vector space over a field $\mathbb{F}$ (where $\mathbb{F}$ is typically the real numbers $\mathbb{R}$). A **linear combination** of a finite set of vectors $\{\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k\}$ in $V$ is an expression formed by multiplying each vector by a scalar weight $c_i \in \mathbb{F}$ and summing the results. Formally, a vector $\mathbf{w} \in V$ is a linear combination of the vectors $\{\mathbf{

---

### Inner Product

**Definition.**
Let $V$ be a vector space over the field $\mathbb{F}$ (where $\mathbb{F}$ is either $\mathbb{R}$ or $\mathbb{C}$). An **inner product** on $V$ is a mapping $\langle \cdot, \cdot \rangle: V \times V \to \mathbb{F}$ that satisfies the following three axioms for all $\mathbf{u}, \mathbf{v}, \mathbf{w} \in V$ and $\alpha \in \mathbb{F}$:

1.  **Linearity in the first argument**: $\langle \alpha\mathbf{u} + \mathbf{v}, \mathbf{w} \rangle = \alpha\langle \mathbf{u}, \mathbf{w} \rangle + \langle \mathbf{v}, \mathbf{w} \rangle$.
2.  **Conjugate Symmetry**: $\langle \mathbf{u}, \mathbf{v} \rangle = \overline{\langle \mathbf{v}, \mathbf{u} \rangle}$. (Note: If $\mathbb{F} = \mathbb{R}$, this simplifies to symmetry: $\langle \mathbf{u}, \mathbf{v} \rangle = \langle \mathbf{v}, \mathbf{u} \rangle$).
3.  **Positive Definiteness**: $\langle \mathbf{v}, \mathbf{v} \rangle \geq 0$ for all $\mathbf{v} \in V$, and $\langle \mathbf{v}, \mathbf{v} \rangle = 0$ if and only if $\mathbf{v} = \mathbf{0}$.

The inner product allows us to define the norm (length) of a vector as $\|\mathbf{v}\| = \sqrt{\langle \mathbf{v}, \mathbf{v} \rangle}$.

**Worked Example.**
Consider the vector space $\mathbb{R}^2$ and a weighted inner product defined by:
$$\langle \mathbf{u}, \mathbf{v} \rangle = 3u_1v_1 + 5u_2v_2$$
where $\mathbf{u} = (u_1, u_2)$ and $\mathbf{v} = (v_1, v_2)$. Let $\mathbf{u} = (1, 2)$ and $\mathbf{v} = (3, -1)$.

To compute the inner product:
$$\langle \mathbf{u}, \mathbf{v} \rangle = 3(1)(3) + 5(2)(-1) = 9 - 10 = -1$$
Note that while the magnitude of the components is large, the specific weighting of the space determines the geometric relationship between vectors.

**Theorem (Cauchy-Schwarz Inequality).**
For any vector space $V$ equipped with an inner product $\langle \cdot, \cdot \rangle$, and for all $\mathbf{u}, \mathbf{v} \in V$, the following inequality holds:
$$|\langle \mathbf{u}, \mathbf{v} \rangle| \leq \|\mathbf{u}\| \|\mathbf{v}\|$$
Equality holds if and only if $\mathbf{u}$ and $\mathbf{v}$ are linearly dependent. This theorem is fundamental in defining the angle $\theta$ between two vectors: $\cos \theta = \frac{\langle \mathbf{u}, \mathbf{v} \rangle}{\|\mathbf{u}\| \|\mathbf{v}\|}$.

**Lab Cell (SymPy)**
The following cell calculates a weighted inner product and the corresponding norm of a vector in $\mathbb{R}^2$.
```python
import sympy as sp

def weighted_inner_product(u, v):
    # Weights for the inner product are [3, 5]
    weights = sp.Matrix([3, 5])
    return u * weights + v*0 # This is a simplification; let's use explicit indices
    
u = sp.Matrix([1, 2])
v = sp.Matrix([3, -1])

# Defining inner product: 3*u1*v1 + 5*u2*v2
inner_prod = 3*u[0]*v[0] + 5*u[1]*v[1]
norm_u = sp.sqrt(3*u[0]**2 + 5*u[1]**2)

print(f"Inner Product: {inner_prod}")
print(f"Norm of u: {norm_u}")
```

---

### Linear Independence

**Definition.** Let $V$ be a vector space over a field $\mathbb{F}$. A set of vectors $\{\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k\} \subseteq V$ is said to be **linearly independent** if the only solution to the vector equation
$$c_1\mathbf{v}_1 + c_2\mathbf{v}_2 + \cdots + c_k\mathbf{v}_k = \mathbf{0}$$
is the trivial solution $c_1 = c_2 = \dots = c_k = 0$, where each $c_i \in \mathbb{F}$. If there exists at least one $c_i \neq 0$ such that the sum equals the zero vector, the set is **linearly dependent**. Effectively, a linearly independent set contains no "redundant" information: no vector in the set can be expressed as a linear combination of the others.

**Worked Example.** To determine if the vectors $\mathbf{v}_1 = \begin{bmatrix} 1 \\ 0 \\ -2 \end{bmatrix}$ and $\mathbf{v}_2 = \begin{bmatrix} 2 \\ 1 \\ -4 \end{bmatrix}$ are linearly independent in $\mathbb{R}^3$, we examine the equation $c_1\mathbf{v}_1 + c_2\mathbf{v}_2 = \mathbf{0}$:
$$c_1 \begin{bmatrix} 1 \\ 0 \\ -2 \end{bmatrix} + c_2 \begin{bmatrix} 2 \\ 1 \\ -4 \end{bmatrix} = \begin{bmatrix} 0 \\ 0 \\ 0 \end{bmatrix}$$
This yields the following system of linear equations:
$$\begin{cases} c_1 + 2c_2 = 0 \\ c_2 = 0 \\ -2c_1 - 4c_2 = 0 \end{cases}$$
From the second equation, we find $c_2 = 0$. Substituting this into the first equation gives $c_1 + 2(0) = 0$, implying $c_1 = 0$. Since both coefficients must be zero to satisfy the equality, the set $\{\mathbf{v}_1, \mathbf{v}_2\}$ is **linearly independent**.

**Key Theorem (The Determinant Criterion).** Let $\mathcal{S} = \{\mathbf{v}_1, \dots, \mathbf{v}_n\}$ be a set of $n$ vectors in $\mathbb{F}^n$. Let $A$ be the $n \times n$ matrix whose columns are these vectors. The set $\mathcal{S}$ is linearly independent if and only if $\det(A) \neq 0$.

*Proof Sketch:* By the Invertible Matrix Theorem, a square matrix $A$ has a non-zero determinant if and only if it is invertible. If $A$ is invertible, the equation $A\mathbf{c} = \mathbf{0}$ has only the trivial solution $\mathbf{c} = A^{-1}\mathbf{0} = \mathbf{0}$. Thus, the absence of a non-zero determinant precludes any non-trivial linear combination resulting in the zero vector.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define vectors as columns of a matrix
v1 = sp.Matrix([1, 0, -2])
v2 = sp.Matrix([2, 1, -4])
A = sp.Matrix([[1, 2], [0, 1], [-2, -4]])

# Verify independence via rank
# A set of n vectors is independent if the rank equals the number of vectors
rank = A.rank()
is_independent = (rank == A.ncols)

print(f"Matrix rank: {rank}")
print(f"Are vectors linearly independent? {is_independent}")

# Alternatively, check determinant for a square matrix (if it were 2x2)
# M = sp.Matrix([[1, 2], [0, 1]])
# print(f"Determinant: {M.det()}")
```

---

### Linear Maps

**Definition.** Let $V$ and $W$ be vector spaces over a field $\mathbb{F}$. A function $T: V \to W$ is called a **linear map** (or linear transformation) if it preserves the structure of vector addition and scalar multiplication. Specifically, for all vectors $\mathbf{u}, \mathbf{v} \in V$ and all scalars $c \in \mathbb{F}$, the map must satisfy:
1. **Additivity**: $T(\mathbf{u} + \mathbf{v}) = T(\mathbf{u}) + T(\mathbf{v})$
2. **Homogeneity**: $T(c\mathbf{u}) = cT(\mathbf{u})$

These two properties can be combined into a single requirement: $T$ is linear if and only if $T(c\mathbf{u} + \mathbf{v}) = cT(\mathbf{u}) + T(\mathbf{v})$ for all $\mathbf{u}, \mathbf{v} \in V$ and $c \in \mathbb{F}$. A fundamental consequence of these axioms is that if $T$ is linear, then $T(\mathbf{0}_V) = \mathbf{0}_W$.

**Worked Example.** Consider a mapping $T: \mathbb{R}^2 \to \mathbb{R}^2$ defined by the rule $T(x, y) = (x + 2y, 3x - y)$. We wish to verify that $T$ is a linear map. Let $\mathbf{u} = (x_1, y_1)$ and $\mathbf{v} = (x_2, y_2)$ be arbitrary vectors in $\mathbb{R}^2$, and let $k \in \mathbb{R}$ be a scalar.
Checking additivity:
$$T(\mathbf{u} + \mathbf{v}) = T(x_1+x_2, y_1+y_2) = ((x_1+x_2) + 2(y_1+y_2), 3(x_1+x_2) - (y_1+y_2))$$
$$= (x_1 + 2y_1 + x_2 + 2y_2, 3x_1 - y_1 + 3x_2 - y_2)$$
$$= (x_1+2y_1, 3x_1-y_1) + (x_2+2y_2, 3x_2-y_2) = T(\mathbf{u}) + T(\mathbf{v})$$
Checking homogeneity:
$$T(k\mathbf{u}) = T(kx_1, ky_1) = (kx_1 + 2ky_1, 3kx_1 - ky_1) = k(x_1+2y_1, 3x_1-y_1) = kT(\mathbf{u})$$
Since both conditions are satisfied, $T$ is a linear map.

**Theorem (Matrix Representation).** Let $V$ and $W$ be finite-dimensional vector spaces over $\mathbb{F}$ with chosen bases $\mathcal{B} = \{\mathbf{v}_1, \dots, \mathbf{v}_n\}$ and $\mathcal{C} = \{\mathbf{w}_1, \dots, \mathbf{w}_m\}$, respectively. For every linear map $T: V \to W$, there exists a unique matrix $A \in M_{m \times n}(\mathbb{F})$ such that for any vector $\mathbf{x} \in V$:
$$[T(\mathbf{x})]_{\mathcal{C}} = A [\mathbf{x}]_{\mathcal{B}}$$
This theorem establishes the fundamental correspondence between abstract linear maps and concrete matrix algebra.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define dimensions and a linear transformation matrix
# Corresponding to T(x, y) = (x + 2y, 3x - y)
A = sp.Matrix([[1, 2], [3, -1]])

# Define an input vector
v = sp.Matrix([1, 2])

# Compute the transformation
w = A * v

print(f"Input vector: {v}")
print(f"Transformed vector: {w}")

# Verify linearity: T(u + v) == T(u) + T(v)
u = sp.Matrix([1, 0])
distinct_v = sp.Matrix([2, 1])
assert (A * (u + distinct_v)) == (A * u) + (A * distinct_v)
print("Linearity verified.")
```

---

### The Span of a Set of Vectors

**Definition.** Let $V$ be a vector space over a field $\mathbb{F}$, and let $S = \{v_1, v_2, \dots, v_k\}$ be a set of vectors in $V$. The **span** of $S$, denoted by $\text{span}(S)$, is the set of all possible linear combinations of the vectors in $S$:
$$\text{span}(S) = \{ c_1v_1 + c_2v_2 + \dots + c_kv_k \mid c_i \in \mathbb{F} \}$$
Geometrically, if $S$ contains a single non-zero vector in $\mathbb{R}^3$, its span is the line passing through that vector and the origin. If $S$ contains two non-parallel vectors, its span is the plane containing both.

**Worked Example.** Consider the subspace $\mathbb{R}^3$ and the set of vectors $S = \{ \mathbf{v}_1, \mathbf{v}_2 \}$ where:
$$\mathbf{v}_1 = \begin{bmatrix} 1 \\ 0 \\ 1 \end{bmatrix}, \quad \mathbf{v}_2 = \begin{bmatrix} 0 \\ 1 \\ 1 \end{bmatrix}$$
Any vector $\mathbf{w}$ in $\text{span}(S)$ must take the form:
$$\mathbf{w} = c_1\begin{bmatrix} 1 \\ 0 \\ 1 \end{bmatrix} + c_2\begin{bmatrix} 0 \\ 1 \\ 1 \end{bmatrix} = \begin{bmatrix} c_1 \\ c_2 \\ c_1 + c_2 \end{bmatrix}$$
To determine if the vector $\mathbf{x} = [1, 2, 3]^T$ lies in $\text{span}(S)$, we solve for $c_1, c_2$:
$$c_1 = 1, \quad c_2 = 2, \quad c_1 + c_2 = 3$$
Since $1+2=3$, the system is consistent; therefore, $\mathbf{x} \in \text{span}(S)$. Conversely, a vector such as $[1, 2, 4]^T$ would not be in the span because $1+2 \neq 4$.

**Theorem.** The span of any set of vectors $S \subseteq V$ is a subspace of $V$.
*Proof Sketch:* To prove $\text{span}(S)$ is a subspace, we check three conditions: (i) The zero vector $\mathbf{0}$ is in the span (set all coefficients $c_i = 0$); (ii) If $\mathbf{u}, \mathbf{w} \in \text{span}(S)$, then their sum $\mathbf{u}+\mathbf{w}$ is a linear combination of elements in $S$, thus $\mathbf{u}+\mathbf{w} \in \text{span}(S)$; and (iii) If $\mathbf{u} \in \text{span}(S)$ and $k \in \mathbb{F}$, then $k\mathbf{u}$ is a linear combination of elements in $S$, thus $k\mathbf{u} \in \text{span}(S)$.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define the vectors in our set S
v1 = sp.Matrix([1, 0, 1])
v2 = sp.Matrix([0, 1, 1])
S = [v1, v2]

# A point to check: x = [1, 2, 3]
x = sp.Matrix([1, 2, 3])

# Using the rank method to check if x is in span(S)
# If rank(A) == rank(A|x), then x is in span(S)
A = sp.Matrix([[v[0] for v in S]]).T # Construct matrix from set
# A correctly formed as a matrix of columns:
A_matrix = sp.Matrix([[1, 0], [0, 1], [1, 1]])
augmented = A_matrix.row_join(x)

print(f"Rank of basis matrix: {A_matrix.rank()}")
print(f"Rank of augmented matrix: {augmented.rank()}")

if A_matrix.rank() == augmented.rank():
    print("The vector is in the span.")
else:
    print("The vector is NOT in the span.")
```

---

\section{The Concept of a Basis}

\subsection{Definition}
Let $V$ be a vector space over a field $\mathbb{F}$. A set of vectors $\mathcal{B} = \{v_1, v_2, \dots, v_n\} \subseteq V$ is called a \textbf{basis} for $V$ if it satisfies the following two conditions:
\begin{enumerate}
    \item \textbf{Linear Independence:} The only scalars $c_1, c_2, \dots, c_n \in \mathbb{F}$ satisfying $\sum_{i=1}^n c_i v_i = \mathbf{0}$ are $c_1 = c_2 = \dots = c_n = 0$.
    \item \textbf{Spanning Property:} Every vector $x \in V$ can be expressed as a linear combination of the elements of $\mathcal{B}$. That is, $\text{span}(\mathcal{B}) = V$.
\end{enumerate}
In essence, a basis provides a "coordinate system" for the vector space. It is the minimal set of vectors necessary to reach every point in $V$ while ensuring that each representation is unique.

\subsection{Worked Example}
Consider the vector space $\mathbb{R}^2$ and the set of vectors $\mathcal{B} = \{\mathbf{v}_1, \mathbf{v}_2\}$ where $\mathbf{v}_1 = \begin{pmatrix} 1 \\ 1 \end{pmatrix}$ and $\mathbf{v}_2 = \begin{pmatrix} 1 \\ -1 \end{pmatrix}$.

To prove $\mathcal{B}$ is a basis:
\begin{enumerate}
    \item \textbf{Linear Independence:} Assume $c_1 \begin{pmatrix} 1 \\ 1 \end{pmatrix} + c_2 \begin{pmatrix} 1 \\ -1 \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix}$. This leads to the system:
    $$c_1 + c_2 = 0, \quad c_1 - c_2 = 0$$
    Adding the equations yields $2c_1 = 0 \implies c_1 = 0$, which forces $c_2 = 0$. Thus, $\mathcal{B}$ is linearly independent.
    \item \textbf{Spanning:} For any vector $\mathbf{x} = \begin{pmatrix} x_1 \\ x_2 \end{pmatrix} \in \mathbb{R}^2$, we seek $c_1, c_2$ such that:
    $$c_1 + c_2 = x_1, \quad c_1 - c_2 = x_2$$
    Solving for the coefficients gives $c_1 = \frac{x_1 + x_2}{2}$ and $c_2 = \frac{x_1 - x_2}{2}$. Since such $c_i$ exist for any $\mathbf{x}$, $\mathcal{B}$ spans $\mathbb{R}^2$.
\end{enumerate}

\subsection{Key Theorem}
\textbf{Theorem (Uniqueness of Representation):} Let $\mathcal{B} = \{v_1, \dots, v_n\}$ be a basis for $V$. For every $x \in V$, there exists a \textit{unique} set of scalars $c_1, \dots, c_n \in \mathbb{F}$ such that $x = \sum_{i=1}^n c_i v_i$.

\begin{proof Sketch}
Suppose $x$ has two representations: $\sum c_i v_i = \sum d_i v_i$. By subtractivity, $\sum (c_i - d_i)v_i = \mathbf{0}$. Since $\{v_1, \dots, v_n\}$ is a basis, it is linearly independent. Therefore, $c_i - d_i = 0$ for all $i$, implying $c_i = d_i$.
\end{proof}

\subsection{Lab Cell (SymPy)}
The following code checks if a set of vectors in $\mathbb{R}^n$ forms a basis by verifying that the matrix formed by these vectors is non-singular.

\begin{verbatim}
import sympy as sp

def is_basis(vectors, dimension):
    """
    Checks if a list of vectors forms a basis for R^n.
    :param vectors: List of lists (e.g., [[1, 1], [1, -1]])
    :param dimension: The dimension of the target space (e.g., 2)
    """
    matrix = sp.Matrix(vectors)
    # A set is a basis if it has 'dimension' vectors and they are linearly independent
    if matrix.shape[0] != dimension:
        return False
    
    # Check rank; for a square matrix, rank must equal the dimension
    rank = matrix.rank()
    return rank == dimension

# Example usage
v1 = [1, 1]
v2 = [1, -1]
print(f"Is basis: {is_basis([v1, v2], 2)}") # Expected: True
\end{verbatim}

---

### Definition: Vector Norm
A **norm** is a function that assigns a non-negative real number to every vector in a vector space, effectively quantifying the "length" or "magnitude" of that vector. Let $V$ be a vector space over the field $\mathbb{F}$ (where $\mathbb{F}$ is $\mathbb{R}$ or $\mathbb{C}$). A mapping $\|\cdot\|: V \to \mathbb{R}$ is defined as a norm if it satisfies the following three axioms for all $u, v \in V$ and all scalars $\alpha \in \mathbb{F}$:

1. **Positive Definiteness**: $\|v\| \geq 0$, and $\|v\| = 0$ if and only if $v = \mathbf{0}$.
2. **Absolute Homogeneity**: $\|\alpha v\| = |\alpha| \|v\|$.  
3. **Triangle Inequality**: $\|u + v\| \leq \|u\| + \|v\|$.

The triangle inequality is the most critical property for analysis, as it ensures that the shortest path between two points in a space defined by this norm is a straight line. Common examples include the $L^p$ norms on $\mathbb{R}^n$, such as the Euclidean norm ($\|x\|_2 = \sqrt{\sum |x_i|^2}$) and the Taxicab norm ($\|x\|_1 = \sum |x_i|$).

### Worked Example
Consider the vector space $\mathbb{R}^3$ and a specific vector $\mathbf{v} = (3, -4, 0)$. We will calculate the magnitude of $\mathbf{v}$ under different norms to see how the choice of norm affects the geometric interpretation:

1. **Euclidean Norm ($p=2$):**
   $$\|\mathbf{v}\|_2 = \sqrt{|3|^2 + |-4|^2 + |0|^2} = \sqrt{9 + 16 + 0} = \sqrt{25} = 5$$
2. **Taxicab Norm ($p=1$):**
   $$\|\mathbf{v}\|_1 = |3| + |-4| + |0| = 7$$
3. **Maximum Norm ($p=\infty$):**
   $$\|\mathbf{v}\|_\infty = \max(|3|, |-4|, |0|) = 4$$

While all three values describe the "size" of $\mathbf{v}$, they do so according to different geometric rules (Euclidean distance, city-block distance, and Chebyshev distance).

### Key Theorem: Equivalence of Norms
**Theorem.** Let $V$ be a finite-dimensional vector space over $\mathbb{R}$. Any two norms $\|\cdot\|_a$ and $\|\cdot\|_b$ on $V$ are **equivalent**. 

Formally, there exist positive constants $c_1, c_2 > 0$ such that for all $v \in V$:
$$c_1 \|v\|_a \leq \|v\|_b \leq c_2 \|v\|_a$$

*Proof Sketch:* Because $V$ is finite-dimensional, it is isomorphic to $\mathbb{R}^n$. One can show that every norm on $\mathbb{R}^n$ is bounded above and below by the maximum norm $\|\cdot\|_\infty$ (scaled by some constant). Since any two norms are each comparable to $\|x\|_\infty$, they are necessarily comparable to one another. This ensures that if a set is "bounded" in one norm, it is bounded in all equivalent norms, meaning the underlying topology of the space remains unchanged regardless of the specific choice of $p$-norm.

### Lab cell (SymPy)
```python
import sympy as sp

def calculate_norms(vector_tuple, p_values=[1, 2, float('inf')]):
    """
    Calculates different L^p norms for a given vector in R^n.
    """
    v = sp.Matrix(vector_tuple)
    results = {}
    
    for p in p_values:
        if p == 1:
            results['L1 (Taxicab)'] = sum(abs(x) for x in v)
        elif p == 2:
            results['L2 (Euclidean)'] = sp.sqrt(sum(x**2 for x in v))
        elif p == float('inf'):
            results['L_inf (Max)'] = max(abs(x) for x in v)
            
    return results

# Example usage:
vec = (3, -4, 0)
norms = calculate_norms(vec)
for name, val in norms.items():
    print(f"{name}: {val}")
```

---

### Orthogonality

**Definition.** Let $(V, \langle \cdot, \cdot \rangle)$ be an inner product space over the field $\mathbb{F}$ (where $\mathbb{F} = \mathbb{R}$ or $\mathbb{C}$). Two vectors $u, v \in V$ are said to be **orthogonal**, denoted by $u \perp v$, if their inner product is zero:
$$\langle u, v \rangle = 0.$$
In the specific case of the Euclidean space $\mathbb{R}^n$ equipped with the standard dot product, two vectors $\mathbf{x}, \mathbf{y} \in \mathbb{R}^n$ are orthogonal if:
$$\sum_{i=1}^{n} x_i y_i = 0.$$
Geometrically, in $\mathbb{R}^2$ or $\mathbb{R}^3$, orthogonality implies that the vectors are mutually perpendicular. It is important to note that the zero vector $\mathbf{0}$ is orthogonal to every vector $v \in V$ because $\langle \mathbf{0}, v \rangle = 0$.

**Worked Example.** Consider two vectors in $\mathbb{R}^3$ defined by $\mathbf{u} = (2, -1, 3)$ and $\mathbf{v} = (1, 2, 0)$. We test for orthogonality using the standard inner product:
$$\langle \mathbf{u}, \mathbf{v} \rangle = (2)(1) + (-1)(2) + (3)(0) = 2 - 2 + 0 = 0.$$
Since $\langle \mathbf{u}, \mathbf{v} \rangle = 0$, the vectors $\mathbf{u}$ and $\mathbf{v}$ are orthogonal ($\mathbf{u} \perp \mathbf{v}$). Conversely, consider $\mathbf{w} = (1, 1, 1)$. Since $\langle \mathbf{u}, \mathbf{w} \rangle = 2 - 1 + 3 = 4 \neq 0$, the vector $\mathbf{w}$ is not orthogonal to $\mathbf{u}$.

**Theorem.** Let $V$ be an inner product space. If vectors $u, v \in V$ are orthogonal ($u \perp v$), then the Pythagorean Theorem holds:
$$\|u + v\|^2 = \|u\|^2 + \|v\|^2.$$
*Proof Sketch:* By the definition of the norm in terms of the inner product, $\|w\|^2 = \langle w, w \rangle$. Expanding the expression for $u+v$:
$$\|u + v\|^2 = \langle u + v, u + v \rangle = \langle u, u \rangle + \langle u, v \rangle + \langle v, u \rangle + \langle v, v \rangle.$$
By the definition of orthogonality, $\langle u, v \rangle = 0$ and (since symmetry/conjugate symmetry holds) $\langle v, u \rangle = 0$. The expression simplifies to:
$$\|u + v\|^2 = \|u\|^2 + 0 + 0 + \|v\|^2 = \|u\|^2 + \|v\|^2.$$

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define the vectors as symbols/elements of R^3
u = sp.Matrix([2, -1, 3])
v = sp.Matrix([1, 2, 0])

# Calculate the inner product
inner_prod = u.dot(v)
print(f"Inner product: {inner_prod}")

# Check if they are orthogonal
is_orthogonal = inner_prod == 0
print(f"Are u and v orthogonal? {is_orthogonal}")

# Verify Pythagoras: ||u + v||^2 == ||u||**2 + ||v||**2
left_side = (u + v).norm()**2
right_side = u.norm()**2 + v.norm()**2
print(f"Pythagorean check: {left_side} == {right_side}")
```

---

### The Adjoint Operator

**Definition.** Let $\mathcal{V}$ be a finite-dimensional inner product space over the field $\mathbb{C}$. For every linear operator $T: \mathcal{V} \to \mathcal{V}$, there exists a unique linear operator $T^*: \mathcal{V} \to \mathcal{V}$, called the *adjoint* of $T$, such that the following identity holds for all vectors $v, w \in \mathcal{V}$:
$$\langle Tv, w \rangle = \langle v, T^*w \rangle$$
When $\mathcal{V} = \mathbb{C}^n$ and we equip it with the standard inner product $\langle a, b \rangle = \sum_{i=1}^n a_i \bar{b}_i$, the adjoint of a linear operator $T$ represented by a matrix $A$ is given by the conjugate transpose:
$$A^* = \overline{A^T}$$
In the specific case where $\mathcal{V}$ is a real inner product space (where the field is $\mathbb{R}$), the adjoint $T^*$ corresponds to the standard transpose $A^T$.

**Worked Example.** Let $A$ be a linear operator on $\mathbb{C}^2$ represented by the matrix:
$$A = \begin{pmatrix} 1 & 2i \\ 3 & 4i \end{pmatrix}$$
To find the adjoint $A^*$, we take the transpose and conjugate each entry:
$$A^T = \begin{pmatrix} 1 & 3 \\ 2i & 4i \end{pmatrix} \implies A^* = \overline{\begin{pmatrix} 1 & 3 \\ 2i & 4i \end{pmatrix}} = \begin{pmatrix} 1 & 3 \\ -2i & -4i \end{pmatrix}$$
To verify this satisfies $\langle Av, w \rangle = \langle v, A^*w \rangle$, let $v = \begin{pmatrix} 1 \\ i \end{pmatrix}$ and $w = \begin{pmatrix} 1 \\ 1 \end{pmatrix}$.
First, compute $Av$:
$$Av = \begin{pmatrix} 1 & 2i \\ 3 & 4i \end{pmatrix} \begin{pmatrix} 1 \\ i \end{pmatrix} = \begin{pmatrix} 1 + 2i^2 \\ 3 + 4i^2 \end{pmatrix} = \begin{pmatrix} -1 \\ -1 \end{pmatrix}$$
Then, $\langle Av, w \rangle = (-1)(1) + (-1)(1) = -2$.
Now compute $A^*w$:
$$A^*w = \begin{pmatrix} 1 & 3 \\ -2i & -4i \end{pmatrix} \begin{pmatrix} 1 \\ 1 \end{pmatrix} = \begin{pmatrix} 4 \\ -6i \end{pmatrix}$$
Then, $\langle v, A^*w \rangle = (1)(\bar{4}) + (i)(\overline{-6i}) = 4 + i(6i) = 4 - 6 = -2$.
The values match, confirming the definition.

**Theorem.** Let $A$ and $B$ be matrices representing linear operators on $\mathcal{V}$. The adjoint of a product of operators is the product of their adjoints in reverse order:
$$(AB)^* = B^* A^*$$
*Proof Sketch:* By the definition of the adjoint, for any vector $x \in \mathcal{V}$ and $y \in \mathcal{V}$, we have:
$$\langle ABx, y \rangle = \langle Bx, A^*y \rangle$$
Applying the definition of the adjoint again to the operator $B$ and the vector $(A^*y)$, we obtain:
$$\langle Bx, A^*y \rangle = \langle x, B^*(A^*y) \rangle = \langle x, (B^*A^*)y \rangle$$
Since this holds for all $x, y$, it follows that $(AB)^* = B^*A^*$.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define the matrices
A = sp.Matrix([[1, .2*sp.I], [3, 4*sp.I]])
B = sp.Matrix([[1, 0], [0, 2]])

# Calculate adjoints (conjugate transpose)
A_star = A.H
B_star = B.H

# Verify (AB)* = B*A*
LHS = (A * B).H
RHS = B_star * A_star

print(f"Adjoint of AB: {LHS}")
print(f"Product of B* and A*: {RHS}")
assert LHS == RHS
```

---

### The Eigenpair

**Definition: Eigenpair**
Let $V$ be a vector space over a field $\mathbb{F}$ (typically $\mathbb{R}$ or $\mathbb{C}$) and let $A \in \mathbb{M}_{n \times n}(\mathbb{F})$ be a square matrix representing a linear operator. An **eigenvalue** is a scalar $\lambda \in \mathbb{F}$ such that there exists a non-zero vector $\mathbf{v} \in V$ satisfying the equation:
$$A\mathbf{v} = \lambda \mathbf{v}$$
The vector $\mathbf{v}$ is called an **eigenvector** associated with $\lambda$. The ordered pair $(\lambda, \mathbf{v})$ is referred to as an **eigenpair**. Geometrically, if $T$ is the linear transformation defined by $A$, then $\mathbf{v}$ represents a direction in the domain that remains invariant under the action of $T$, modified only by the scale factor $\lambda$. It is critical by definition that $\mathbf{v} \neq \mathbf{0}$, as the zero vector trivially satisfies the equation for any $\lambda$ and provides no information regarding the transformation’s geometry.

**Worked Example**
Consider the matrix $A = \begin{pmatrix} 4 & 2 \\ 1 & 3 \end{pmatrix}$. To find the eigenpairs, we first determine the eigenvalues by solving the characteristic equation $\det(A - \lambda I) = 0$:
$$\det \begin{pmatrix} 4-\lambda & 2 \\ 1 & 3-\lambda \end{pmatrix} = (4-\lambda)(3-\lambda) - 2 = \lambda^2 - 7\lambda + 10 = 0$$
Factorizing the quadratic gives $(\lambda-5)(\lambda-2)=0$, yielding eigenvalues $\lambda_1 = 5$ and $\lambda_2 = 2$.

To find the eigenvector $\mathbf{v}_1$ for $\lambda_1=5$, we solve $(A - 5I)\mathbf{x} = \mathbf{0}$:
$$\begin{pmatrix} -1 & 2 \\ 1 & -2 \end{pmatrix} \begin{pmatrix} x_1 \\ x_2 \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix} \implies x_1 = 2x_2$$
A representative eigenvector is $\mathbf{v}_1 = \begin{pmatrix} 2 \\ 1 \end{pmatrix}$.  
For $\lambda_2=2$, we solve $(A - 2I)\mathbf{x} = \mathbf{0}$:
$$\begin{pmatrix} 2 & 2 \\ 1 & 1 \end{pmatrix} \begin{pmatrix} x_1 \\ x_2 \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix} \implies x_1 = -x_2$$
A representative eigenvector is $\mathbf{v}_2 = \begin{pmatrix} 1 \\ -1 \end{pmatrix}$.  
The resulting eigenpairs are $(5, [2, 1]^\top)$ and $(2, [1, -1]^\top)$.

**Key Theorem: The Characteristic Equation**
*Theorem:* Let $A$ be an $n \times n$ matrix. A scalar $\lambda$ is an eigenvalue of $A$ if and only if the characteristic polynomial $p(\lambda) = \det(A - \lambda I)$ satisfies $p(\lambda) = 0$.

*Proof Sketch:* The condition $A\mathbf{v} = \lambda\mathbf{v}$ can be rearranged as $(A - \lambda I)\mathbf{v} = \mathbf{0}$. This represents a homogeneous system of linear equations. For a non-zero solution $\mathbf{v}$ to exist, the matrix $(A - \lambda I)$ must be singular (non-invertible). By the Fundamental Theorem of Linear Algebra, a square matrix is singular if and only if its determinant is zero. Thus, $\lambda$ must be a root of $\det(A - \lambda I)$.

**Lab cell (SymPy)**
```python
import sympy as sp

# Define the matrix A
A = sp.Matrix([[4, 2], [1, 3]])

# Find eigenvalues and eigenvectors
eigen_vals, eigen_vecs = A.eigenvects()

print(f"Eigenvalues: {list(eigen_vals)}")
print(f"Eigenvectors: {eigen_vecs}")
```

---

### Orthonormal Basis

**Definition: Orthonormal Basis**
Let $(V, \langle \cdot, \cdot \rangle)$ be an inner product space. A set of vectors $\mathcal{B} = \{\mathbf{u}_1, \mathbf{u}_2, \dots, \mathbf{u}_n\}$ in $V$ is said to be **orthogonal** if the inner product of any two distinct vectors in $\mathcal{B}$ is zero:
$$\langle \mathbf{u}_i, \mathbf{u}_j \rangle = 0 \quad \text{for } i \neq j.$$
The set $\mathcal{B}$ is said to be **orthonormal** if it is orthogonal and every vector in the set has a unit norm ($\|\mathbf{u}_i\| = 1$). Formally, $\mathcal{B}$ is an orthonormal basis for $V$ if:
$$\langle \mathbf{u}_i, \mathbf{u}_j \rangle = \delta_{ij}$$
where $\delta_{ij}$ is the Kronecker delta ($\delta_{ij} = 1$ if $i=j$, and $0$ otherwise). An orthonormal basis provides a geometric "grid" where coordinate calculation is simplified because each basis vector behaves independently.

**Worked Example**
Consider the subspace $W \subset \mathbb{R}^3$ spanned by the vectors $\mathbf{v}_1 = (2, 2, 0)$ and $\mathbf{v}_2 = (-1, 1, 0)$. We wish to construct an orthonormal basis $\{\mathbf{q}_1, \mathbf{q}_2\}$ for $W$.
First, we verify orthogonality: $\langle \mathbf{v}_1, \mathbf{v}_2 \rangle = (2)(-1) + (2)(1) + (0)(0) = 0$. The vectors are orthogonal.
Next, we normalize each vector by dividing by its magnitude:
$\|\mathbf{v}_1\| = \sqrt{2^2 + 2^2 + 0^2} = \sqrt{8} = 2\sqrt{2}$
$\|\mathbf{v}_2\| = \sqrt{(-1)^2 + 1^2 + 0^2} = \sqrt{2}$
The resulting orthonormal basis is:
$$\mathbf{q}_1 = \frac{\mathbf{v}_1}{\|\mathbf{v}_1\|} = \left(\frac{1}{\sqrt{2}}, \frac{1}{\sqrt{2}}, 0\right), \quad \mathbf{q}_2 = \frac{\mathbf{v}_2}{\|\mathbf{v}_2\|} = \left(-\frac{1}{\sqrt{2}}, \frac{1}{\sqrt{2}}, 0\right)$$
Testing the condition: $\langle \mathbf{q}_1, \mathbf{q}_1 \rangle = \frac{1}{2} + \frac{1}{2} = 1$ and $\langle \mathbf{q}_1, \mathbf{q}_2 \rangle = -\frac{1}{2} + \frac{1}{2} = 0$.

**Theorem: Expansion in Orthonormal Bases**
Let $V$ be a finite-dimensional inner product space with an orthonormal basis $\mathcal{B} = \{\mathbf{e}_1, \dots, \mathbf{e}_n\}$. For any vector $\mathbf{x} \in V$, the unique representation of $\mathbf{x}$ in terms of $\mathcal{B}$ is given by:
$$\mathbf{x} = \sum_{i=1}^n \langle \mathbf{x}, \mathbf{e}_i \rangle \mathbf{e}_i$$
*Proof Sketch:* Since $\mathcal{B}$ is a basis, $\mathbf{x} = \sum c_j \mathbf{e}_j$. Taking the inner product of both sides with $\mathbf{e}_i$ yields $\langle \mathbf{x}, \mathbf{e}_i \rangle = \sum c_j \langle \mathbf{e}_j, \mathbf{e}_i \rangle$. By the orthonormality property ($\delta_{ij}$), all terms in the sum vanish except for $j=i$, leaving $\langle \mathbf{x}, \mathbf{e}_i \rangle = c_i(1)$.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define a set of vectors in R3
v1 = sp.Matrix([2, 2, 0])
v2 = sp.Matrix([-1, 1, 0])

# Gram-Schmidt Orthogonalization Step (Normalizing existing orthogonal basis)
q1 = v1 / v1.norm()
q2 = v2 / v2.norm()

# Verification of Orthonormal properties
ortho_check = q1.dot(v1.norm()) # Should be 1
cross_check = q1.dot(q2)        # Should be 0

print(f"Norm of q1: {orth_check}")
print(f"Dot product q1 . q2: {cross_check}")
```

---

## Payoff

### The Spectral Theorem: The Synthesis of Symmetry and Dynamics

**Definition.** Let $V$ be a finite-dimensional inner product space over $\mathbb{R}$ (or $\mathbb{C}$) and let $A \in \mathbb{R}^{n \times n}$ be a symmetric matrix ($A = A^T$). The Spectral Theorem states that there exists an orthonormal basis $\{u_1, \dots, u_n\}$ of $V$ consisting of eigenvectors of $A$. Consequently, $A$ can be decomposed as:
$$A = Q \Lambda Q^T = \sum_{i=1}^{n} \lambda_i u_i u_i^T$$
where $Q$ is an orthogonal matrix ($Q^TQ = I$) and $\Lambda$ is a diagonal matrix containing the real eigenvalues $\lambda_j$. This decomposition implies that a symmetric operator acts only by scaling along mutually perpendicular axes, effectively "decoupling" the coordinate system into independent physical modes.

**Worked Example.** Consider the symmetric matrix representing a physical system’s stress:
$$A = \begin{pmatrix} 3 & 1 \\ 1 & 3 \end{pmatrix}$$
Calculating the characteristic polynomial $\det(A - \lambda I) = (3-\lambda)^2 - 1 = 0$ yields eigenvalues $\lambda_1=4$ and $\lambda_2=2$. The corresponding normalized eigenvectors are $u_1 = \frac{1}{\sqrt{2}}[1, 1]^T$ and $u_2 = \frac{1}{\sqrt{2}}[1, -1]^T$. Since $A$ is symmetric, these vectors are orthogonal ($\langle u_1, u_2 \rangle = 0$). The spectral decomposition allows us to view the transformation as a scaling of factor 4 along the line $y=x$ and a scaling of factor 2 along $y=-x$.

**Key Theorem: Symmetry $\implies$ Observability.**
The Spectral Theorem is the crowning achievement of this text because it bridges internal algebraic structure with external physical reality. In **quantum_observable** contexts, any physical quantity that can be measured (e.g., energy, position) must be represented by a Hermitian operator (the complex extension of symmetric matrices). The spectral theorem ensures these observables have real eigenvalues—yielding measurable values—and orthogonal eigenstates, ensuring distinct physical states are unambiguous. 

In **fourier_modes**, the transition from discrete to continuous systems occurs through this same logic. A signal can be viewed as an evolution under a differential operator (like the Laplacian $\nabla^2$). Because the Laplacian is symmetric (self-adjoint), its eigenfunctions—the sine and cosine waves of Fourier analysis—form an orthogonal basis. Spectral decomposition thus allows us to decompose complex time-series into independent "modes" or frequencies, just as it decomposes $A$ into eigenvalues.

**Lab Cell (SymPy)**
```python
import sympy as sp

# Define a symmetric matrix representing a physical system
A = sp.Matrix([[3, 1], [1, 3]])

# Extract eigenvalues and eigenvectors
eigen_vals, eigen_vecs = A.eigs()

# Print the spectral decomposition components
print(f"Eigenvalues: {eigen_vals}")
print(f"Normalized Eigenvectors: {eigen_vecs}")

# Verification of orthogonality (Q.T @ Q == I)
Q = sp.Matrix([[eigen_vecs[i][0] for i in range(len(eigen_vecs))] for i in range(2)]) # Simplified representation
```