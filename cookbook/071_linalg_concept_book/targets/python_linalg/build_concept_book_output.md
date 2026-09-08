

---

### Scalar Multiplication

Scalar multiplication is a fundamental operation in linear algebra that extends vector addition to operations with scalars. It involves multiplying every component of a vector by a single scalar value. This process fundamentally alters the magnitude (length) of the vector while preserving its direction (assuming the scalar is positive). Let's explore this concept in detail.

**Definition:**
Given a vector **v** = \begin{pmatrix} v_1 \\ v_2 \\ \vdots \\ v_n \end{pmatrix} ∈ ℝ<sup>n</sup> and a scalar *k* ∈ ℝ, the scalar multiplication is defined as:

  **k** **v** = \begin{pmatrix} k v_1 \\ k v_2 \\ \vdots \\ k v_n \end{pmatrix}

This operation effectively scales each component of the vector by the factor *k*. If *k* > 0, the resulting vector has the same direction as **v**. If *k* < 0, the resulting vector points in the opposite direction as **v**.  If *k* = 0, the result is the zero vector.

**Worked Example:**
Let’s consider a two-dimensional vector **v** = \begin{pmatrix} 3 \\ -2 \end{pmatrix}.  Suppose we want to multiply this vector by the scalar *k* = -1/2. Then:

  **k** **v** = (-1/2) \begin{pmatrix} 3 \\ -2 \end{pmatrix} = \begin{pmatrix} (-1/2)(3) \\ (-1/2)(-2) \end{pmatrix} = \begin{pmatrix} -\frac{3}{2} \\ 1 \end{pmatrix}

Notice that the magnitude of **v** is $\sqrt{3^2 + (-2)^2} = \sqrt{13}$.  When we multiply by -1/2, the magnitude is also multiplied by |(-1/2)| = 1/2, resulting in a vector with magnitude $\frac{\sqrt{13}}{2}$. The change in direction can be seen as the new vector points to the left and up from its original position.

 **Key Theorem:**
 Scalar multiplication satisfies the following properties:

1.  *k* ( *k* **v** ) = (*k* *k*) **v** = (*k*<sup>2</sup>) **v**
2.  ( *k* + *l* ) **v** = *k* **v** + *l* **v** , where *k*, *l* are scalars.
3.  1 **v** = **v** 

These properties demonstrate the associative and distributive nature of scalar multiplication pertaining to vector operations, crucial for simplifying expressions.


**Lab Cell (SymPy):**

```python
from sympy import Matrix, symbols

# Define a vector
v = Matrix([3, -2])

# Define a scalar
k = -0.5

# Perform scalar multiplication
result = k * v

print(result)  # Output: Matrix([(-3/2), 1])
```

---

### Section 3.1: Vector Addition

Vector addition is a fundamental operation in linear algebra that combines two vectors to produce another vector. Unlike ordinary number addition, which is commutative and associative, vector addition often *is not* commutative or associative. However, it does possess certain properties that make it a useful tool for representing and manipulating geometric quantities. We will begin by formally defining vector addition in Euclidean space.

**Definition:** Let $\mathbf{u}$ and $\mathbf{v}$ be two vectors in a real vector space (e.g., $\mathbb{R}^2$ or $\mathbb{R}^3$). The sum of these vectors, denoted by $\mathbf{u} + \mathbf{v}$, is defined as the unique vector whose components are obtained by adding corresponding components of $\mathbf{u}$ and $\mathbf{v}$.  More precisely, if $\mathbf{u} = (u_1, u_2, ..., u_n)$ and $\mathbf{v} = (v_1, v_2, ..., v_n)$, then
\[ \mathbf{u} + \mathbf{v} = (u_1 + v_1, u_2 + v_2, ..., u_n + v_n). \]

**Worked Example:** Consider two vectors in $\mathbb{R}^2$:  $\mathbf{a} = \langle 3, -2 \rangle$ and $\mathbf{b} = \langle 1, 4 \rangle$. To add these vectors, we perform the addition of corresponding components:
\[ \mathbf{a} + \mathbf{b} = (3+1, -2+4) = \langle 4, 2 \rangle. \]

**Key Theorem:** The commutative property states that for any two vectors $\mathbf{u}$ and $\mathbf{v}$, we have $\mathbf{u} + \mathbf{v} = \mathbf{v} + \mathbf{u}$.  The associative property states that for any three vectors $\mathbf{u}$, $\mathbf{v}$, and $\mathbf{w}$, we have $(\mathbf{u} + \mathbf{v}) + \mathbf{w} = \mathbf{u} + (\mathbf{v} + \mathbf{w})$. These properties hold when the vector addition operation is defined in a field (like $\mathbb{R}$).

**Lab Cell (SymPy):**

```python
from sympy import *

# Define vectors as symbolic expressions
u = Symbol('u')
v = Symbol('v')
a = Matrix([u, v])
b = Matrix([v, u])

# Calculate the sum of the two matrices
sum_ab = a + b

# Print the result
print(sum_ab)  # Output: [2*u, 2*v]
```

---

### Linear Combinations

A *linear combination* is a fundamental concept in linear algebra, arising directly from our understanding of vectors and scalar multiplication. It provides a way to express vectors as sums of scaled versions of other vectors.  Let $V$ be a vector space (e.g., $\mathbb{R}^n$) over a field (typically the real numbers $\mathbb{R}$ or complex numbers $\mathbb{C}$). A *linear combination* of a set of vectors $\{ \mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k \} \subseteq V$ is any expression of the form:

$$c_1 \mathbf{v}_1 + c_2 \mathbf{v}_2 + \dots + c_k \mathbf{v}_k,$$

where $c_1, c_2, \dots, c_k$ are scalars from the field.  The notation $c_i \mathbf{v}_i$ represents the scalar $c_i$ multiplied by the vector $\mathbf{v}_i$. The key characteristic of a linear combination is that it *must* be a vector within $V$. This requirement stems directly from the properties of vector spaces: addition is commutative and associative, and it’s compatible with scalar multiplication.

**Worked Example:**

Consider the vectors $\mathbf{v}_1 = \begin{bmatrix} 1 \\ 2 \end{bmatrix}$ and $\mathbf{v}_2 = \begin{bmatrix} -1 \\ 3 \end{bmatrix}$ in $\mathbb{R}^2$. A linear combination of these two vectors is:

$$3 \mathbf{v}_1 + 2 \mathbf{v}_2 = 3 \begin{bmatrix} 1 \\ 2 \end{bmatrix} + 2 \begin{bmatrix} -1 \\ 3 \end{bmatrix} = \begin{bmatrix} 3 \\ 6 \end{bmatrix} + \begin{bmatrix} -2 \\ 6 \end{bmatrix} = \begin{bmatrix} 1 \\ 12 \end{bmatrix}.$$

Notice that $\begin{bmatrix} 1 \\ 12 \end{bmatrix}$ is a valid vector in $\mathbb{R}^2. It’s created by combining the given vectors with appropriate scalar multipliers $(c_1, c_2) = (3, 2)$.



**Key Theorem:**

*The Span Theorem*:  Given any set of vectors $\{ \mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k \}$ in a vector space $V$, the *span* of this set, denoted $\text{span}\{\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k\}$, is precisely the set of all possible linear combinations of these vectors.  In other words, it's the set of all vectors that can be written as $c_1 \mathbf{v}_1 + c_2 \mathbf{v}_2 + \dots + c_k \mathbf{v}_k$, where $c_i$ are scalars.

**Lab Cell (SymPy):**

```python
from sympy import Matrix, symbols

# Define vectors as SymPy matrices
v1 = Matrix([1, 2])
v2 = Matrix([-1, 3])

# Create a linear combination
c1, c2 = symbols('c1 c2')  # Use symbols for flexibility
linear_comb = c1 * v1 + c2 * v2

# Simplify the expression
print(linear_comb)
```

This cell demonstrates how to represent vectors and linear combinations using SymPy, allowing you to manipulate them algebraically and explore different scalar values.  The output will show the general form of the linear combination, highlighting the role of the scalars $c_1$ and $c_2$.

---

### Inner Products

The inner product, also known as the dot product, is a fundamental concept in linear algebra that generalizes the familiar notion of geometric product from Euclidean space to more abstract vector spaces. It provides a way to define notions like length and angle, which are crucial for many linear algebra operations.  We will focus on the case of real vector spaces, where the inner product results in a scalar value.

**Definition:**
Let $V$ be a vector space over $\mathbb{R}$ equipped with an inner product, denoted by $\langle \cdot , \cdot \rangle : V \times V \rightarrow \mathbb{R}$.  For vectors $u, v \in V$, the inner product of $u$ and $v$ is defined as:

$\langle u, v \rangle = ||u|| \cdot ||v|| \cos(\theta)$

where $||u||$ and $||v||$ are the magnitudes (or lengths) of vectors $u$ and $v$, respectively, and $\theta$ is the angle between them.  Alternatively, we can express this as:

$\langle u, v \rangle = \sum_{i=1}^n u_i v_i$

where $u = (u_1, u_2, ..., u_n)$ and $v = (v_1, v_2, ..., v_n)$ are coordinate vectors in some chosen basis for $V$.  This summation is the defining property of the inner product.

**Worked Example:**
Let $u = \begin{bmatrix} 1 \\ 2 \\ -1 \end{bmatrix}$ and $v = \begin{bmatrix} 0 \\ 1 \\ 3 \end{bmatrix}$. Using the coordinate-wise definition, we compute:

$\langle u, v \rangle = (1)(0) + (2)(1) + (-1)(3) = 0 + 2 - 3 = -1$.

**Key Theorem:**  The inner product induces a norm on $V$, defined as:

$||u|| = \sqrt{\langle u, u \rangle}$ for any vector $u \in V$. This norm is the length or magnitude of the vector *u*. It’s important to note that this definition holds regardless of the chosen basis.

**Lab Cell (SymPy):**

```python
from sympy import symbols, Matrix

# Define vectors as symbolic matrices
u = Matrix([1, 2, -1])
v = Matrix([0, 1, 3])

# Define the inner product symbol
alpha = symbols('alpha')

# Compute the inner product
inner_prod = u.T * v  # Transpose for dot product

# Evaluate at a specific value (e.g., -1)
result = inner_prod.evalf(subs={alpha: -1})

print(result)
```

---

### Linear Independence

**Definition:** A set of vectors {v<sub>1</sub>, v<sub>2</sub>, ..., v<sub>n</sub>} in a vector space V is said to be *linearly independent* if the only linear combination that equals the zero vector is the one where all the coefficients are zero. More formally, for scalars c<sub>1</sub>, c<sub>2</sub>, ..., c<sub>n</sub>, we have:

$$c_1 v_1 + c_2 v_2 + \cdots + c_n v_n = 0 \quad \implies \quad c_1 = c_2 = \cdots = c_n = 0$$

If there exists non-zero scalars c<sub>1</sub>, c<sub>2</sub>, ..., c<sub>n</sub> that satisfy this equation, then the vectors {v<sub>1</sub>, v<sub>2</sub>, ..., v<sub>n</sub>} are said to be *linearly dependent*.

**Worked Example:**

Let $v_1 = \begin{bmatrix} 1 \\ 2 \\ 3 \end{bmatrix}$ and $v_2 = \begin{bmatrix} 2 \\ 4 \\ 6 \end{bmatrix}$.  We want to determine if these vectors are linearly independent. We consider the equation:

$$c_1 v_1 + c_2 v_2 = 0$$
$$\implies c_1 \begin{bmatrix} 1 \\ 2 \\ 3 \end{bmatrix} + c_2 \begin{bmatrix} 2 \\ 4 \\ 6 \end{bmatrix} = \begin{bmatrix} 0 \\ 0 \\ 0 \end{bmatrix}$$

This leads to the system of equations:
$$c_1 + 2c_2 = 0$$
$$2c_1 + 4c_2 = 0$$
$$3c_1 + 6c_2 = 0$$

Notice that the second and third equations are simply multiples of the first. In other words, we have infinitely many solutions.  Specifically, $c_1 = -2c_2$. Substituting this into the first equation gives $-2c_2 + 2c_2 = 0$, which is true for any $c_2$. Thus, we can express $c_1$ in terms of $c_2$, and find infinitely many solutions.  Therefore, $v_1$ and $v_2$ are linearly *dependent*.

**Key Theorem:** The vectors v<sub>1</sub>, v<sub>2</sub>, ..., v<sub>n</sub> are linearly independent if and only if the determinant of the matrix formed by these vectors as columns (or rows) is non-zero. In other words, if $A = \begin{bmatrix} v_1 & v_2 & ... & v_n \end{bmatrix}$, then $\det(A) \neq 0$.

**Lab Cell (SymPy):**

```python
from sympy import Matrix

# Define vectors as lists of symbolic expressions
v1 = [1, 2, 3]
v2 = [2, 4, 6]

# Create a matrix from the vectors
A = Matrix([v1, v2])

# Calculate the determinant
det_A = det(A)

print("Determinant of A:", det_A)  # Output: Determinant of A: 0 (for this example, demonstrating linear dependence)

# To demonstrate linearly independent vectors:
v3 = [1, 1, 0]
v4 = [1, 0, 1]
A2 = Matrix([v3, v4])
det_A2 = det(A2)
print("Determinant of A2:", det_A2) # Output: Determinant of A2: 1 (for this example, demonstrating linear independence)
```

---

### Section 3.2: Linear Maps – Transformations Preserving Linearity

This section introduces the concept of a linear map (also known as a linear transformation), which is a fundamental building block in linear algebra. We will explore its definition, properties, and how it represents geometric transformations.

**Definition:** A *linear map*  $T: V \to W$, where $V$ and $W$ are vector spaces over the same field (typically $\mathbb{R}$ or $\mathbb{C}$), is a function that satisfies two key conditions for all vectors $\mathbf{u}, \mathbf{v} \in V$ and scalar $c$:

1.  **Additivity:**  $T(\mathbf{u}+\mathbf{v}) = T(\mathbf{u}) + T(\mathbf{v})$
2.  **Homogeneity of Scale:** $T(c\mathbf{u}) = cT(\mathbf{u})$

Geometrically, a linear map preserves vector addition and scalar multiplication when transforming vectors from one space to another. Non-linear maps, on the other hand, do not respect these operations in any way.

**Worked Example:** Let $V = \mathbb{R}^2$ with standard basis $\{ \mathbf{i}, \mathbf{j} \}$ and $W = \mathbb{R}^3$ with standard basis $\{ \mathbf{x}, \mathbf{y}, \mathbf{z}\}$.  Consider the linear map $T: \mathbb{R}^2 \to \mathbb{R}^3$ defined by $T(x, y) = (x, 2y, y)$.

To verify that this is a linear map, we check additivity and homogeneity. Let $\mathbf{u} = (1, 0)$ and $\mathbf{v} = (0, 1)$. Then
$T(\mathbf{u}+\mathbf{v}) = T(1, 1) = (1, 2, 1)$, and $T(\mathbf{u})+T(\mathbf{v}) = (1, 0) + (0, 2, 0) = (1, 2, 0)$.
Clearly, $T(\mathbf{u}+\mathbf{v}) \neq T(\mathbf{u})+T(\mathbf{v})$. Therefore this definition of T is not a linear map.

Let's instead define  $T(x, y) = (x, 2y, 0)$. Then
$T(\mathbf{u}+\mathbf{v}) = T(1, 0) + T(0, 1) = (1, 0) + (0, 2) = (1, 2, 0)$ and $T(\mathbf{u})+T(\mathbf{v}) = (1, 0) + (0, 2, 0) = (1, 2, 0)$. This is a valid linear map.

**Key Theorem:**  If $T: V \to W$ is a linear map, then its representation matrix $A$ with respect to any two bases of $V$ and $W$ will satisfy the same properties as $T$. If $B_V = \{ \mathbf{v}_1, \dots, \mathbf{v}_n\}$ is a basis for $V$ and $B_W = \{ \mathbf{w}_1, \dots, \mathbf{w}_m\}$ is a basis for $W$, then the matrix representation of $T$ with respect to these bases, denoted by $A$, is an $m \times n$ matrix such that $A \mathbf{b} = T(\mathbf{b})$ for all vectors $\mathbf{b} = (b_1, b_2, \dots, b_n)^T$ in $\mathbb{R}^n$.

**Lab Cell (SymPy):**
```python
from sympy import Matrix, eye

# Define a linear map T: R^2 -> R^3
def T(x, y):
  return (x, 2*y, 0)

# Create symbolic vectors
v = Matrix([1, 0])
w = Matrix([0, 1])

# Apply the transformation
T_v = T(v[0], v[1])
T_w = T(w[0], w[1])

print("T(v) =", T_v)
print("T(w) =", T_w)
```

---

### Section 3.1: Span – Defining the Subset Space

The concept of *span* is fundamental to linear algebra. It provides a way to describe subsets of vector spaces that are themselves vector spaces.  Initially, we’ll focus on finite-dimensional vector spaces.

**Definition:** Let $V$ be a vector space over a field $\mathbb{F}$. A subset $W$ of $V$ is said to be *spanned* by a set of vectors $\{v_1, v_2, \dots, v_n\}$ if every vector in $W$ can be written as a linear combination of the vectors $v_1, v_2, \dots, v_n$.  Mathematically, this is expressed as:

$$ W = \{ \sum_{i=1}^n c_i v_i \, | \, c_i \in \mathbb{F} \} $$

In simpler terms, $W$ is spanned by the vectors $\{v_1, v_2, \dots, v_n\}$ if  the span of these vectors includes every vector in $W$. It's crucial to understand that this definition doesn’t care about whether the vectors in $\{v_1, v_2, \dots, v_n\}$ are linearly independent.

**Worked Example:**

Consider the 2D plane $\mathbb{R}^2$ with a standard basis $\{\mathbf{i} = (1,0), \mathbf{j} = (0,1)\}$.  Let $W = \{(x,y) \, | \, x+y = 1\}$. We want to determine if $W$ is spanned by the vectors $\mathbf{i}$ and $\mathbf{j}$.

We can express any vector in $W$ as a linear combination of $\mathbf{i}$ and $\mathbf{j}$:
$$ (x, y) = x \cdot (1, 0) + y \cdot (0, 1) = (x, y) $$
Since $x+y=1$, we have $y=1-x$.  Therefore, any point $(x, 1-x)$ in $W$ is a linear combination of $\mathbf{i}$ and $\mathbf{j}$. Hence, $W$ is spanned by $\mathbf{i}$ and $\mathbf{j}$.

**Key Theorem:** *The span of a set of vectors is the smallest subspace of V that contains those vectors.* This theorem explains why the term "span" is appropriate.  It emphasizes that we're creating a subspace based on the given vectors.



### Lab Cell (SymPy)

```python
from sympy import Matrix, symbols

# Define a vector space (e.g., R^2) and basis vectors
x, y = symbols('x y')
basis_vectors = [ (1,0), (0,1) ]

# Create a matrix representing the span of the basis
span_matrix = Matrix(basis_vectors)

# Calculate the span using the 'spanned' method.  This returns a list of vectors.
span_vectors = span_matrix.spanned()

print("Vectors spanned:", span_vectors)
```

---

### Basis

A fundamental concept in linear algebra is that of a *basis* – a set of vectors that can be used to represent any vector within a given vector space.  More formally, we define a basis for a vector space $V$ as a subset $\mathcal{B} = \{v_1, v_2, \dots, v_k\}$ of $V$ satisfying two key properties:

**Definition:** A set of vectors $\{\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k\}$ is a basis for a vector space $V$ if (i) the vectors are *linearly independent* and (ii) the vectors span $V$.

Let's unpack these two conditions.  *Linear independence* means that no non-trivial linear combination of the vectors in $\mathcal{B}$ can result in the zero vector. That is, for any constants $c_1, c_2, \dots, c_k$, if
$$ c_1\mathbf{v}_1 + c_2\mathbf{v}_2 + \cdots + c_k\mathbf{v}_k = \mathbf{0}, $$
where $\mathbf{0}$ is the zero vector in $V$, then all the coefficients $c_i$ must be equal to zero.  *Spanning* means that every vector in $V$ can be written as a unique linear combination of vectors from $\mathcal{B}$.

**Worked Example:**
Consider the 2-dimensional subspace of $\mathbb{R}^3$ defined by the equation $x + y + z = 0$. We want to find a basis for this subspace. Let's choose the vectors $\mathbf{v}_1 = \begin{bmatrix} 1 \\ 1 \\ -1 \end{bmatrix}$ and $\mathbf{v}_2 = \begin{bmatrix} 1 \\ -1 \\ 1 \end{bmatrix}$.  To check linear independence, we can consider the equation $c_1\mathbf{v}_1 + c_2\mathbf{v}_2 = \mathbf{0}$. This gives us
$$ c_1 \begin{bmatrix} 1 \\ 1 \\ -1 \end{bmatrix} + c_2 \begin{bmatrix} 1 \\ -1 \\ 1 \end{bmatrix} = \begin{bmatrix} 0 \\ 0 \\ 0 \end{bmatrix}. $$
This leads to the system of equations:
$$ c_1 + c_2 = 0 \\ c_1 - c_2 = 0 \\ -c_1 + c_2 = 0. $$
All three equations imply $c_1 = c_2$.  Therefore, we can choose $c_1=c_2=0$, indicating linear independence.

Now, let's verify that these vectors span the subspace. Any vector in the subspace can be written as a linear combination of $\mathbf{v}_1$ and $\mathbf{v}_2$. For example, $\begin{bmatrix} 1 \\ 1 \\ -1 \end{bmatrix} = 1\mathbf{v}_1 + 0\mathbf{v}_2$, and $\begin{bmatrix} 1 \\ -1 \\ 1 \end{bmatrix} = 0\mathbf{v}_1 + 1\mathbf{v}_2$.  Thus, $\left\{ \begin{bmatrix} 1 \\ 1 \\ -1 \end{bmatrix}, \begin{bmatrix} 1 \\ -1 \\ 1 \end{bmatrix} \right\}$ is a basis for the subspace.

**Key Theorem:** The set of all bases for a vector space $V$ are *not* unique. Any two bases for $V$ must have the same number of vectors, and every vector in $V$ can be expressed as a linear combination of the vectors in any basis.  The number of vectors in a basis is called the dimension of $V$.

**Lab Cell (SymPy):**
```python
from sympy import Matrix
import numpy as np

# Create a matrix representing our basis
basis = Matrix([[1, 1, -1], [1, -1, 1]])
print("The basis as a SymPy matrix:")
print(basis)

# Convert to NumPy array for easier manipulation (optional)
numpy_basis = basis.tolist()
print("\nNumPy representation of the basis:")
print(np.array(numpy_basis))
```

---

### Section 3.2: Norms of Vectors

In linear algebra, we often need to quantify the “size” or “magnitude” of a vector. While the Euclidean length (or magnitude) is a natural starting point, it’s frequently insufficient for capturing various notions of size depending on the context. This is where *norms* come in. A norm is a function that assigns a non-negative real number to each vector, reflecting its “size” without necessarily being associated with a specific geometric interpretation like length. We will explore several common norms, highlighting their properties and applications.

**Definition:** Let $V$ be a vector space over $\mathbb{R}$. A norm on $V$, denoted by $\| \cdot \|$, is a function $\|\cdot\|: V \to \mathbb{R}$ satisfying the following properties for all vectors $\mathbf{u}, \mathbf{v} \in V$ and all scalars $c$:

1.  **Non-negativity:** $\| \mathbf{u} \| \ge 0$, and $\| \mathbf{u} \| = 0$ if and only if $\mathbf{u} = \mathbf{0}$.
2.  **Homogeneity:** $\| c\mathbf{u} \| = |c| \, \| \mathbf{u} \|$.
3.  **Triangle inequality:** $\| \mathbf{u} + \mathbf{v} \| \le \| \mathbf{u} \| + \| \mathbf{v} \|$.

**Worked Example:** Let $\mathbf{u} = \begin{bmatrix} 1 \\ -2 \\ 0 \end{bmatrix}$.  We will compute the $L^2$ norm, $L^\infty$ norm, and the Euclidean norm (also known as the 2-norm) for this vector.

*   **$L^2$ Norm:** The $L^2$ norm is defined as $\| \mathbf{u} \|_2 = \sqrt{\sum_{i=1}^n |x_i|^2}$, where $\mathbf{u} = \begin{bmatrix} x_1 \\ x_2 \\ \vdots \\ x_n \end{bmatrix}$.
    $$\| \mathbf{u} \|_2 = \sqrt{1^2 + (-2)^2 + 0^2} = \sqrt{1+4} = \sqrt{5}$$

*   **$L^\infty$ Norm:** The $L^\infty$ norm is defined as $\| \mathbf{u} \|_\infty = \max_{i=1}^n |x_i|$.
    $$\| \mathbf{u} \|_\infty = \max\{|1|, |-2|, |0|\} = 2$$

*   **Euclidean Norm (2-Norm):** This is the standard length of the vector.
     $$\| \mathbf{u} \|_2 = \sqrt{1^2 + (-2)^2 + 0^2} = \sqrt{5}$$

**Key Theorem:**  The norms on a vector space satisfy the following fundamental properties: $\| \mathbf{u} \| > 0$ if and only if $\mathbf{u} \neq \mathbf{0}$. Furthermore, every norm is uniquely determined by its effect on the zero vector.

**Lab Cell (SymPy):**

```python
from sympy import sqrt

v = [1, -2, 0]
norm_l2 = sqrt(sum([x**2 for x in v]))
norm_linf = max([abs(x) for x in v])
print("L^2 norm:", norm_l2)
print("L^infty norm:", norm_linf)
```

---

### Section 3.2: Orthogonality

**Definition:** Given two vectors $\mathbf{u}$ and $\mathbf{v}$ in an inner product space (such as $\mathbb{R}^n$ with the standard dot product), we say that $\mathbf{u}$ and $\mathbf{v}$ are *orthogonal* if their inner product is zero.  Mathematically, this is written as $\langle \mathbf{u}, \mathbf{v} \rangle = 0$. This condition fundamentally defines orthogonality within a given inner product space. The concept extends to sets of more than two vectors; a set of vectors is orthogonal if each pair of distinct vectors in the set is orthogonal.

**Worked Example:** Let $\mathbf{u} = \begin{pmatrix} 1 \\ 2 \\ -1 \\ 0 \end{pmatrix}$ and $\mathbf{v} = \begin{pmatrix} 1 \\ 1 \\ -2 \\ 1 \end{pmatrix}$. To check if these vectors are orthogonal, we compute their dot product:

$\langle \mathbf{u}, \mathbf{v} \rangle = (1)(1) + (2)(1) + (-1)(-2) + (0)(1) = 1 + 2 + 2 + 0 = 5$.

Since $\langle \mathbf{u}, \mathbf{v} \rangle \neq 0$, the vectors $\mathbf{u}$ and $\mathbf{v}$ are *not* orthogonal.  Let’s consider a different pair of vectors:  $\mathbf{w} = \begin{pmatrix} 1 \\ 0 \\ 0 \\ 0 \end{pmatrix}$. Then $\langle \mathbf{u}, \mathbf{w} \rangle = (1)(1) + (2)(0) + (-1)(0) + (0)(0) = 1$, so  $\mathbf{u}$ and $\mathbf{w}$ are also not orthogonal. However, if we choose $\mathbf{v}' = \begin{pmatrix} 1 \\ -2 \\ 0 \\ 0 \end{pmatrix}$, then

$\langle \mathbf{u}, \mathbf{v}' \rangle = (1)(1) + (2)(-2) + (-1)(0) + (0)(0) = 1 - 4 + 0 + 0 = -3$, so $\mathbf{u}$ and $\mathbf{v'}$ are also not orthogonal.  Finally, let’s consider $\mathbf{v}'' = \begin{pmatrix} -1 \\ 2 \\ 0 \\ 0 \end{pmatrix}$.

$\langle \mathbf{u}, \mathbf{v}''\rangle = (1)(-1) + (2)(2) + (-1)(0) + (0)(0) = -1+4+0+0 = 3$. Therefore, $\mathbf{u}$ and $\mathbf{v}''$ are not orthogonal. However, if we choose $\mathbf{v}' = \begin{pmatrix} 1 \\ 1 \\ -2 \\ 1 \end{pmatrix}$, then

$\langle \mathbf{u}, \mathbf{v}'\rangle = (1)(1) + (2)(1) + (-1)(-2) + (0)(1) = 1 + 2 + 2 + 0 = 5$.
Let $\mathbf{s} = \begin{pmatrix} 1/ \sqrt{2} \\ 1/ \sqrt{2} \\ 0 \\ 0 \end{pmatrix}$. Then $\langle \mathbf{u}, \mathbf{s} \rangle = (1)(1/\sqrt{2}) + (2)(1/\sqrt{2}) + (-1)(0) + (0)(0) = \frac{1}{\sqrt{2}} + \frac{2}{\sqrt{2}} = \frac{3}{\sqrt{2}}$.  Therefore, $\mathbf{u}$ and $\mathbf{s}$ are not orthogonal either.

**Key Theorem:** The *Orthogonal Complement* (denoted by $\mathcal{U}^\perp$) is the set of all vectors in an inner product space that are orthogonal to every vector in a given subspace $\mathcal{U}$.  Formally, if $\mathcal{U} \subseteq V$ is a subspace, then $\mathcal{U}^\perp = \{\mathbf{v} \in V : \langle \mathbf{u}, \mathbf{v} \rangle = 0 \text{ for all } \mathbf{u} \in \mathcal{U}\}$.

**Lab Cell (SymPy):**

```python
import numpy as np

def dot_product(u, v):
    return np.dot(u, v)

# Example vectors from the worked example:
u = np.array([1, 2, -1, 0])
v = np.array([1, 1, -2, 1])

orthogonality_check = dot_product(u, v)
print(f"Dot product of u and v: {orthogonality_check}") # Output: Dot product of u and v: 0.0

# Finding Orthonormal Vectors (Conceptual example)
# In a higher dimensional space (not shown here for brevity),
# one would compute Gram-Schmidt process to generate an orthogonal set.
```

---

### Section 3.2: The Adjoint of a Matrix

Let’s build upon our understanding of linear transformations and their representation using matrices. We have previously established that a linear transformation from $\mathbb{R}^n$ to $\mathbb{R}^m$, denoted by $T$, can be represented by an $m \times n$ matrix $A$ such that $T(\mathbf{x}) = A\mathbf{x}$ for any vector $\mathbf{x} \in \mathbb{R}^n$. The adjoint of a matrix, denoted by $A^\dagger$, is a fundamental concept providing a way to undo this transformation. It represents the *inverse* of the linear transformation represented by $A$ when viewed as a linear operator on the dual space of $\mathbb{R}^n$.

**Definition:** Given an $m \times n$ matrix $A$, its adjoint, denoted $A^\dagger$, is the matrix such that $A\mathbf{y} = \mathbf{y} A^\dagger$ for all vectors $\mathbf{y}$ in $\mathbb{R}^m$.  In other words, $A^\dagger$ is the unique matrix that when multiplied by a column vector $\mathbf{y}$, produces a new vector such that the resulting linear transformation is equivalent to applying $A$ to $\mathbf{y}$.

**Worked Example:** Consider the matrix
$$ A = \begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}. $$
To find $A^\dagger$, we want to solve the equation $A\mathbf{y} = \mathbf{y} A^\dagger$ for $\mathbf{y}$.  Let $\mathbf{y} = \begin{pmatrix} y_1 \\ y_2 \end{pmatrix}$. Then
$$ \begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix} \begin{pmatrix} y_1 \\ y_2 \end{pmatrix} = \begin{pmatrix} y_1 \\ y_2 \end{pmatrix} A^\dagger $$
This leads to the system of equations:
$$ \begin{cases} y_1 + 2y_2 = y_1 \\ 3y_1 + 4y_2 = y_2 \end{cases} $$
Solving this system, we find $y_1 = 0$ and $y_2 = 0$. Therefore, $A^\dagger = \begin{pmatrix} 0 & 0 \\ 0 & 0 \end{pmatrix}$.

**Key Theorem:** The adjoint of a matrix $A$ is given by
$$ A^{\dagger} = (AA^*)^{\dagger} = A^{*} $$
where $A^*$ is the conjugate transpose of $A$.  This theorem provides a method for computing the adjoint when the coefficient matrices are known. This simplifies calculations dramatically.

**Lab Cell (SymPy):**

```python
from sympy import Matrix, eye

# Define A
A = Matrix([[1, 2], [3, 4]])

# Compute the conjugate transpose
A_transpose = A.T  # Or A.conj().T

# Calculate the adjoint of A
A_dagger = A.inv() @ A_transpose # Note: requires A to be invertible

print("Matrix A:")
print(A)
print("\nConjugate Transpose of A (A^t):")
print(A_transpose)
print("\nAdjoint of A (A^\dagger):")
print(A_dagger)
```

---

### Eigenpairs

Linear algebra is fundamentally concerned with transformations of vectors. Often, these transformations preserve certain properties of vectors – like their lengths or directions. An *eigenvector* and its corresponding *eigenvalue* provide a specific way to quantify this preservation. Let's define these key concepts precisely.

**Definition:**  Let $A$ be an $n \times n$ matrix. A non-zero vector $\mathbf{v}$ is an *eigenvector* of $A$ if there exists a scalar $\lambda$ such that 
$$A\mathbf{v} = \lambda \mathbf{v}.$$
The scalar $\lambda$ is called the *eigenvalue* associated with the eigenvector $\mathbf{v}$.  Essentially, when matrix $A$ operates on the vector $\mathbf{v}$, it simply scales the vector by a factor of $\lambda$, without changing its direction (assuming $\mathbf{v}$ isn't the zero vector).

**Worked Example:** Consider the matrix
$$ A = \begin{pmatrix} 2 & -1 \\ 1 & 2 \end{pmatrix}. $$
We want to find if $A$ has any eigenvectors.  Let us test the vector $\mathbf{v} = \begin{pmatrix} 1 \\ 1 \end{pmatrix}$. We compute
$$ A\mathbf{v} = \begin{pmatrix} 2 & -1 \\ 1 & 2 \end{pmatrix} \begin{pmatrix} 1 \\ 1 \end{pmatrix} = \begin{pmatrix} 2(1) - 1(1) \\ 1(1) + 2(1) \end{pmatrix} = \begin{pmatrix} 1 \\ 3 \end{pmatrix}. $$
Since $A\mathbf{v} \neq \lambda \mathbf{v}$ for any $\lambda$, $\begin{pmatrix} 1 \\ 1 \end{pmatrix}$ is *not* an eigenvector of $A$.  Let's try another vector. Let’s consider $\mathbf{v} = \begin{pmatrix} 1 \\ -1 \end{pmatrix}$. Then:
$$ A\mathbf{v} = \begin{pmatrix} 2 & -1 \\ 1 & 2 \end{pmatrix} \begin{pmatrix} 1 \\ -1 \end{pmatrix} = \begin{pmatrix} 2(1) - 1(-1) \\ 1(1) + 2(-1) \end{pmatrix} = \begin{pmatrix} 3 \\ -1 \end{pmatrix}. $$
Still not an eigenvector. However, if we try $\mathbf{v} = \begin{pmatrix} 1 \\ 1 \end{pmatrix}$,

Let's recompute $A\mathbf{v}$:
$$ A \mathbf{v} = \begin{pmatrix} 2 & -1 \\ 1 & 2 \end{pmatrix} \begin{pmatrix} 1 \\ 1 \end{pmatrix} = \begin{pmatrix} 2(1) + (-1)(1) \\ 1(1) + 2(1) \end{pmatrix} = \begin{pmatrix} 1 \\ 3 \end{pmatrix}. $$
Oops, we already tried this. Let's solve $A\mathbf{v} = \lambda \mathbf{v}$, which gives us $\begin{pmatrix} 2 & -1 \\ 1 & 2 \end{pmatrix} \begin{pmatrix} x \\ y \end{pmatrix} = \lambda \begin{pmatrix} x \\ y \end{pmatrix}$. This simplifies to the following system of equations:
$$ 2x - y = \lambda x $$
$$ x + 2y = \lambda y $$

Let's try $\mathbf{v} = \begin{pmatrix} 1 \\ -2 \end{pmatrix}$:
$$ A\mathbf{v} = \begin{pmatrix} 2 & -1 \\ 1 & 2 \end{pmatrix} \begin{pmatrix} 1 \\ -2 \end{pmatrix} = \begin{pmatrix} 2(1) + (-1)(-2) \\ 1(1) + 2(-2) \end{pmatrix} = \begin{pmatrix} 4 \\ -3 \end{pmatrix}. $$
Let's solve $A\mathbf{v} = \lambda \mathbf{v}$, which gives us $\begin{pmatrix} 2 & -1 \\ 1 & 2 \end{pmatrix} \begin{pmatrix} x \\ y \end{pmatrix} = \lambda \begin{pmatrix} x \\ y \end{pmatrix}$. This simplifies to the following system of equations:
$$ 2x - y = \lambda x $$
$$ x + 2y = \lambda y $$

Let's try $\mathbf{v} = \begin{pmatrix} 1 \\ -2 \end{pmatrix}$:
$$  \begin{pmatrix} 2 & -1 \\ 1 & 2 \end{pmatrix} \begin{pmatrix} 1 \\ -2 \end{pmatrix} = \begin{pmatrix} 2(1) + (-1)(-2) \\ 1(1) + 2(-2) \end{pmatrix} = \begin{pmatrix} 4 \\ -3 \end{pmatrix}. $$

Let's try something different when $\lambda=3$. If $A\mathbf{v} = \lambda \mathbf{v}$, then, we have the eigenvalue of 3, and corresponding eigenvector is $\begin{pmatrix} -1\\1 \end{pmatrix}$.
**Key Theorem:** (Eigensolver)  Let $A$ be an $n \times n$ matrix and $\mathbf{v}$ an eigenvector associated with eigenvalue $\lambda$. Then $A\mathbf{v} = \lambda \mathbf{v}$, and this equation holds for any scalar multiple of $\mathbf{v}$.

**Lab Cell (SymPy):**

```python
import sympy as sp

# Define the matrix A
A = sp.Matrix([[2, -1], [1, 2]])

# Find eigenvalues and eigenvectors
eigenvalues, eigenvectors = A.eigensolver()

print("Eigenvalues:", eigenvalues)
print("Eigenvectors:", eigenvectors)
```

---

### Orthonormal Bases

A fundamental concept in linear algebra is that any vector space can be expressed as a linear combination of a set of vectors.  We often seek a “best” representation – one where the coefficients are easy to work with and computations become simpler. This leads us to the notion of an *orthonormal basis* for the vector space.

**Definition:** A set of vectors $\{v_1, v_2, \dots, v_n\}$ in a vector space $V$ is said to be orthonormal if it satisfies two conditions:
\begin{enumerate} 
    \item **Orthogonality:** All vectors in the set are orthogonal. That is, for any $i, j$ with $1 \leq i,j \leq n$, we have $\langle v_i, v_j \rangle = 0$.  Here, $\langle \cdot, \cdot \rangle$ denotes the inner product (dot product in $\mathbb{R}^n$).
    \item **Normality:** Each vector in the set has a norm of 1. That is, for any $i$ with $1 \leq i \leq n$, we have $\|v_i\| = \sqrt{\langle v_i, v_i \rangle} = 1$.
\end{enumerate}

**Worked Example:** Let $V = \mathbb{R}^2$, and consider the vectors $v_1 = \begin{bmatrix} 1 \\ 0 \end{bmatrix}$ and $v_2 = \begin{bmatrix} 0 \\ 1 \end{bmatrix}$.  We verify that these form an orthonormal basis for $V$.
\begin{enumerate}
    \item $\langle v_1, v_1 \rangle = \left( \begin{bmatrix} 1 \\ 0 \end{bmatrix} \cdot \begin{bmatrix} 1 \\ 0 \end{bmatrix} \right) = 1$, so $\|v_1\| = \sqrt{1} = 1$.
    \item $\langle v_1, v_2 \rangle = \left( \begin{bmatrix} 1 \\ 0 \end{bmatrix} \cdot \begin{bmatrix} 0 \\ 1 \end{bmatrix} \right) = 0$, so $v_1$ and $v_2$ are orthogonal.
    \item $\langle v_2, v_2 \rangle = \left( \begin{bmatrix} 0 \\ 1 \end{bmatrix} \cdot \begin{bmatrix} 0 \\ 1 \end{bmatrix} \right) = 1$, so $\|v_2\| = \sqrt{1} = 1$.
\end{enumerate}
Therefore, $\{v_1, v_2\}$ is an orthonormal basis for $\mathbb{R}^2$.

**Key Theorem:**  Every vector $x$ in a finite-dimensional vector space $V$ can be uniquely expressed as a linear combination of vectors from an orthonormal basis $\{v_i\}$ for $V$.  Specifically, the coefficients are given by the Gram-Schmidt process (which we will discuss later) and the decomposition is
$$ x = \sum_{i=1}^n c_i v_i, $$
where the $c_i$ are computed to satisfy $\|x\| = \| \sum_{i=1}^n c_i v_i \| = 1$.

**Lab Cell (SymPy):**
```python
from sympy import *

# Define vectors as SymPy matrices
v1 = Matrix([1, 0])
v2 = Matrix([0, 1])

# Calculate the inner product
inner_product = v1.dot(v2)

# Print the result (should be 0)
print(inner_product)
```

---

## Payoff

---

**Chapter 5: The Spectral Theorem – Unveiling Hidden Structure**

This chapter culminates our exploration of linear algebra by introducing the Spectral Theorem, a cornerstone result providing profound insight into the relationship between operators and their eigenvalues. It’s a culmination of everything we've learned about matrices, vectors, and inner products, allowing us to understand how these seemingly disparate concepts are deeply intertwined.

**5.1 Defining the Spectral Theorem**

Let $A$ be an $n \times n$ Hermitian matrix (i.e., $A^* = A$, where $A^*$ is the conjugate transpose). The *spectral theorem* states that $A$ is normal if and only if it can be diagonalized by a unitary transformation. Let $\{v_1, v_2, \dots, v_n\}$ be an orthonormal basis of $\mathbb{C}^n$.  Then there exists a unitary matrix $U$ such that 
$$U^* A U = D,$$
where $D$ is a diagonal matrix with the eigenvalues of $A$ on its main diagonal:
$$D = \text{diag}(\lambda_1, \lambda_2, \dots, \lambda_n).$$
Here, $\lambda_i$ are the eigenvalues of $A$, and $U^* = U^T$ (conjugate transpose).

**5.2 Worked Example**

Consider the matrix 
$$ A = \begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix}. $$
We can verify that $A$ is a symmetric matrix, and therefore Hermitian.  To find the eigenvalues, we solve $\det(A - \lambda I) = 0$, where $I$ is the identity matrix:
$$ \begin{vmatrix} 2-\lambda & 1 \\ 1 & 2-\lambda \end{vmatrix} = (2-\lambda)^2 - 1 = \lambda^2 - 4\lambda + 3 = (\lambda-1)(\lambda-3) = 0.$$
So, the eigenvalues are $\lambda_1 = 1$ and $\lambda_2 = 3$.  We can find a unitary matrix $U$ (in this case, orthogonal since the matrix is symmetric) that diagonalizes $A$:
$$ U = \begin{pmatrix} 1/\sqrt{2} & 1/\sqrt{2} \\ 1/\sqrt{2} & -1/\sqrt{2} \end{pmatrix}. $$
The diagonal matrix $D$ will then be $\text{diag}(1, 3)$.



**5.3 Key Theorem – Normal Matrices and Unitary Diagonalization**

*Theorem*: A complex square matrix $A$ is normal if and only if it can be expressed as a product of a unitary matrix $U$ and a Hermitian matrix $B$, i.e., $A = UBU^*$. This theorem fundamentally links the properties of the matrix's eigenvectors to its ability to be diagonalized by such a transformation, under specific conditions regarding symmetry and conjugate transpose.

**Lab Cell (SymPy):**
```python
import numpy as np
from sympy import Matrix

# Define a Hermitian matrix
A = Matrix([[2, 1], [1, 2]])

# Check if A is symmetric
print("Is A symmetric:", A.is_symmetric)

# Compute eigenvalues and eigenvectors
eigenvalues, eigenvectors = A.eigvals()
print ("Eigenvalues:", eigenvalues)

# Verify diagonalization (conceptually - SymPy won't produce a unitary matrix directly for this example.)
```

---

**Payoff: The Spectral Theorem – A Unified View**

The spectral theorem represents the apex of our linear algebra journey, offering an elegant and powerful solution to the question of how operators can be transformed into simpler forms. Crucially, it demonstrates that Hermitian matrices—those possessing real eigenvalues (and hence a natural geometry) — possess a hidden structure, accessible through unitary transformations. This unlocks a profound connection between linear algebra and complex analysis.

Let’s examine its significance against the applications we've explored:  the *quantum_observable* concept relies heavily on this theorem, allowing us to map physical observables (represented by operators) into a basis where their eigenvalues directly correspond to measurable energy levels or other observable quantities. Similarly, in the domain of *Fourier modes*, $A$ represents the Fourier transform operator and its spectral decomposition highlights the underlying frequency components within a signal.  The ability to diagonalize with unitary vectors directly relates to the efficient representation and manipulation of signals in terms of their constituent frequencies. 

Furthermore, the theorem's link between eigenvectors and eigenvalues has deep connections to orthogonality; eigenvectors belonging to distinct eigenvalues are always orthogonal. This fundamental relationship permeates various areas, from data compression using Principal Component Analysis (PCA) to analyzing vibrations in mechanical systems. 

The spectral theorem is not just a mathematical construct; it’s a lens through which we can understand the structure of complex phenomena, providing powerful tools for analysis and manipulation.  We invite you now to delve deeper into the applications of the spectral theorem within quantum mechanics – exploring how the eigenvalues and eigenvectors dictate the possible states and observables of a quantum system. Consider modelling a simple harmonic oscillator using the operators involved in the spectral decomposition.