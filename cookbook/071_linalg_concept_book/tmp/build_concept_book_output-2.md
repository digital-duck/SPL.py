

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

## Payoff

### Payoff: The Significance of Linear Independence

The concept of linear independence serves as the fundamental bridge between computational calculation and abstract structural analysis. While the preceding modules focused on solving for $\mathbf{x}$ in a given system, linear independence reveals the underlying geometry of the space itself. It serves as the definitive mathematical criterion for "non-redundancy." When a set of vectors is linearly independent, each vector provides unique information that cannot be replicated by any combination of the others. This transition marks the culmination of our current study: moving from finding solutions to understanding the integrity and dimensionality of the spaces in which those solutions exist.

The utility of this concept is immediately realized in three core areas of higher mathematics:

1. **Uniqueness of Solutions:** In the linear system $A\mathbf{x} = \mathbf{b}$, the independence of the columns of $A$ dictates whether a solution, if it exists, is unique. If the columns are linearly independent, then $\mathbf{b}$ can be represented as a linear combination of the columns in only one way. This ensures that every coordinate in the vector $\mathbf{x}$ is uniquely determined, a prerequisite for stability in engineering and physics models.

2. **Basis Theory and Dimensionality:** Linear independence is the necessary condition to define a *basis*. A basis is a spanning set that contains no redundant vectors. Without this distinction, we could not define "dimension"—the fundamental measure of how many degrees of freedom exist within a system. This allows us to quantify the size of subspaces ranging from simple planes to complex function spaces.

3. **Kernel and Rank Analysis:** In the study of linear transformations $T: V \to W$, independence allows us to determine exactly how much information is lost or preserved. By identifying independent vectors, we can calculate the rank of a matrix, determining its "reach" in the codomain while simultaneously measuring the size of its kernel (the dimension of the input space that collapses to zero).

Having mastered the criteria for linear independence, you are now equipped to proceed to the study of **Basis and Dimension**, where you will learn how these independent vectors form the skeletal framework of all vector spaces.