

---
Generalidades del Proyecto
Análisis y Diseño de Algoritmos


---
Índice general

I

Introducción

1

Planteamiento . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7

1.1

Entrada de datos

1.1.1
1.1.2

Sistema original . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
Sistema candidato . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8

1.2

Conceptos

1.2.1
1.2.2
1.2.3

Marginalización . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
Probabilidad condicional . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
Distancias Métricas . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14

2

Bipartición . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

17

2.1

Particionamiento

17

7

10


---

---
I

Introducción

1

Planteamiento . . . . . . . . . . . . . . . . . . . . . . . 7

1.1
1.2

Entrada de datos
Conceptos

2

Bipartición . . . . . . . . . . . . . . . . .

2.1

Particionamiento

17


---

---
1. Planteamiento

A lo largo de este documento se buscará que el alumnado comprenda los conceptos requeridos
a lo largo del proyecto abordado en la materia de Análisis y Diseño de Algoritmos para el período
lectivo de 2025C. Así, podrá desenvolverse eficientemente en la resolución del problema principal.

1.1

Entrada de datos

1.1.1

Sistema original
El sistema que abordamos está compuesto por n elementos discretos aunque pueden extenderse
de forma continua si es necesario. Estos elementos, denotados como V = {X1 , X2 , · · · , Xn }, adoptan
un valor binario en el tiempo, es decir, pueden estar activos o inactivos. Para analizar su comportamiento a lo largo del tiempo, utilizamos una Matriz de Probabilidad de Transición (TPM). Esta
matriz nos proporciona las probabilidades de que el sistema evolucione de un estado en el tiempo t
hacia un estado en t + 1, dado un estado inicial conocido.
Es de esta forma que surge la necesidad de ver un elemento en sus dos tiempos independientes,
representable mediante la expansión de la forma V = {(X1 , X2 , · · · , Xn )t+1 , (X1 , X2 , · · · , Xn )t }.
Definition 1.1.1 — Transition Probability Matrix.

Para un sistema V = {A, B,C} la TPM mostrada a continuación representa en cada una de
sus celdas cuál es la probabilidad de llegar a cada estado t + 1 desde cada posible estado en un


---
Capítulo 1. Planteamiento

8

tiempo t indicando si el elemento toma o un valor de uno o cero.
At+1 0 1 0 1 0 1 0 1
Bt+1 0 0 1 1 0 0 1 1
Ct+1 0 0 0 0 1 1 1 1
At
0
1
0
1
0
1
0
1

Bt Ct
0 0
0 0
1 0
1 0
0 1
0 1
1 1
1 1

1
0
0
0
0
0
0
0

0
0
0
1
1
0
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
1

0
1
0
0
0
0
0
0

0
0
1
0
0
0
1
0

0
0
0
0
0
0
0
0

0
0
0
0
0
1
0
0

Example 1.1 Se aprecia cómo la probabilidad con la que el sistema pasa a los estados
At+1 = 0, Bt+1 = 0, Ct+1 = 1 dado el estado inicial At = 1, Bt = 0, Ct = 0 es equivalente a 1
(evento seguro), mientras que la probabilidad de que llegue al estado ABCt+1 = 101 dado el
estado inicial ABCt = 101 equivale a 0 (evento imposible).
■
■

La TPM está en la forma conocida como estado-estado, donde las filas representan los
estados en t, las columnas los estados en t +1 y cada entrada T PM[i][ j] representa la probabilidad
de pasar del estado i ∈ t al j ∈ t + 1.

Se manejará un conjunto n de elementos de forma que permita conocer la distribución de probabilidad de los elementos en los estados de t + 1 tras una serie de operaciones en la TPM sobre otro
conjunto de elementos que condicionarán el sistema. Esto se realizará siempre teniendo en cuenta
un estado inicial, sobre el que se encuentra cada uno de los elementos del sistema. Para facilidad
del programador esta entrada de datos se dará en formato .csv para su lectura inicial.

1.1.2

Sistema candidato

Cuando se selecciona un subconjunto de elementos de tamaño k, donde 0 < k ≤ n, generamos
lo que llamamos un Sistema Candidato. Este sistema incluye solo los elementos que estamos analizando, mientras que los elementos externos se consideran como condiciones de fondo (background
conditions). A partir del estado inicial de los elementos externos, podemos formar y analizar el
comportamiento del Sistema Candidato bajo estas condiciones.

■

Example 1.2

Se parte del sistema V = {A, B,C, D} con estado inicial t = 1000 respectivamente. Se buscará
trabajar con el Sistema candidato Vc = {A, B,C}, se condicionará la TPM en los estados t donde el
elemento D sea igual a 0.


---
1.1 Entrada de datos

9

A
B
C
D
A
0
1
0
1
0
1
0
1
0
1
0
1
0
1
0
1

B
0
0
1
1
0
0
1
1
0
0
1
1
0
0
1
1

C D
0 0
0 0
0 0
0 0
1 0
1 0
1 0
1 0
0 1
0 1
0 1
0 1
1 1
1 1
1 1
1 1
t

0
0
0
0

1
0
0
0

0
1
0
0

1
1
0
0

0
0
1
0

1
0
1
0

0
1
1
0

1
1
1
0

0
0
0
1

1
0
0
1

0
1
0
1

1
1
0
1

0
0
1
1

1
0
1
1

0
1
1
1

1
1
1 t +1
1

1
0
0
0
0
0
0
0
0
0
0
0
0
0
0
0

0
0
0
1
1
0
0
0
0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0
0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
1
0
0
0
0
0
0
0
0

0
1
0
0
0
0
0
0
0
0
0
0
0
0
0
0

0
0
1
0
0
0
1
0
0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0
0
0
0
0
0
0
0
0

0
0
0
0
0
1
0
0
0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0
0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0
1
0
0
1
1
0
0
0

0
0
0
0
0
0
0
0
0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0
0
0
0
0
0
0
0
1

0
0
0
0
0
0
0
0
0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0
0
1
1
0
0
0
1
0

0
0
0
0
0
0
0
0
0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0
0
0
0
0
0
1
0
0

Deberíamos obtener la siguiente TPM condicionada en el t asociado al estado actual del
elemento externo D = 0.

A
B
C
D
A
0
1
0
1
0
1
0
1

B
0
0
1
1
0
0
1
1
t

C
0
0
0
0
1
1
1
1

0
0
0
0

1
0
0
0

0
1
0
0

1
1
0
0

0
0
1
0

1
0
1
0

0
1
1
0

1
1
1
0

0
0
0
1

1
0
0
1

0
1
0
1

1
1
0
1

0
0
1
1

1
0
1
1

0
1
1
1

1
1
1 t +1
1

1
0
0
0
0
0
0
0

0
0
0
1
1
0
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
1

0
1
0
0
0
0
0
0

0
0
1
0
0
0
1
0

0
0
0
0
0
0
0
0

0
0
0
0
0
1
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
0

Ahora se debe aplicar un proceso conocido como la marginalización en la columna asociada
al elemento D en t + 1, este proceso de marginalización será explicado más adelante y nos generará


---
Capítulo 1. Planteamiento

10
la siguiente matriz resultante.

A 0 1 0 1 0 1 0 1
B 0 0 1 1 0 0 1 1 t +1
C 0 0 0 0 1 1 1 1
A
0
1
0
1
0
1
0
1

B
0
0
1
1
0
0
1
1
t

C
0
0
0
0
1
1
1
1

1
0
0
0
0
0
0
0

0
0
0
1
1
0
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
1

0
1
0
0
0
0
0
0

0
0
1
0
0
0
1
0

0
0
0
0
0
0
0
0

0
0
0
0
0
1
0
0

■

1.2

Conceptos
Se presentará en este apartado el contenido necesario para empezar con la manipulación del
sistema a nivel matricial, comprendiendo conceptos aplicados sobre marginalización, probabilidad condicional para descomposición matricial y finalmente métricas para dar comparación a
distribuciones de probabilidad.

1.2.1

Marginalización
En el análisis del sistema, puede ser de interés determinar las probabilidades individuales
de los elementos en t + 1, especialmente bajo la suposición de independencia condicional. Esto
nos permite calcular la probabilidad asociada a un subconjunto r del sistema candidato, donde
0 < r ≤ k. Al hacer esto, esencialmente estamos marginalizando ciertos elementos del sistema, es
decir, los estamos excluyendo del análisis directo para enfocarnos en los elementos de interés.
Para esto la TPM asociada a V podrá ser marginalizada en los tiempos t o t + 1 dependiendo de
los elementos que queremos excluir.
Marginalización respecto a las Filas (t)

Este método se centra en eliminar ciertos elementos del sistema en el tiempo t, permitiendo
analizar y descomponer el comportamiento de los elementos restantes. Al aplicar la marginalización
sobre las filas de la TPM, descartamos las filas correspondientes a los elementos que no nos interesan
en t. Posteriormente, agrupamos los estados resultantes que sean coincidentes para mantener la
coherencia en la matriz.
■

Example 1.3

A 0 1 0 1 0 1 0 1
B 0 0 1 1 0 0 1 1 t +1
C 0 0 0 0 1 1 1 1
A
0
1
0
1
0
1
0
1

B
0
0
1
1
0
0
1
1
t

C
0
0
0
0
1
1
1
1

1
0
0
0
0
0
0
0

0
0
0
1
1
0
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
1

0
1
0
0
0
0
0
0

0
0
1
0
0
0
1
0

0
0
0
0
0
0
0
0

0
0
0
0
0
1
0
0

Consideremos Vc = {A, B,C} como sistema candidato representado por la TPM adjunta. Supongamos que deseamos analizar el
subsistema Vs = {At+1 , Bt+1 ,Ct+1 , At }, manteniendo las columnas ABCt+1 y descartando
las filas correspondientes a Bt y Ct en Vc .


---
1.2 Conceptos

11

En la TPM ahora se aprecia cómo el elemento At presenta repetición de estados o registros, esto debe solventarse mediante aplicación de una operación de agregación, tal
que se promedien los registros por índice.

A 0 1 0 1 0 1 0 1
B 0 0 1 1 0 0 1 1 t +1
C 0 0 0 0 1 1 1 1
A
0
1
0
1
0
1
0
1
t

1
0
0
0
0
0
0
0

0
0
0
1
1
0
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
1

0
1
0
0
0
0
0
0

0
0
1
0
0
0
1
0

0
0
0
0
0
0
0
0

0
0
0
0
0
1
0
0

La TPM resultante será la siguiente, se puede apreciar como aunque se ha llevado una extensión
en Q+ se seguirá manteniendo la probabilidad de encontrar el sistema en un estado t + 1 dado cada
nueva entrada en t ha de sumar 1.
A
B
C
A
0
1
t

0
0
0

1
0
0

0
1
0

1
1
0

0
0
1

1
0
1

0
1
1

1
1
1

t +1

0,25 0,25 0
0
0
0,5 0
0
0
0,25 0 0,25 0,25 0 0 0,25
■

Marginalización respecto a las Columnas (t + 1)

En este método, eliminamos ciertos elementos del sistema en el tiempo t + 1. Al descartar
las columnas correspondientes en la TPM, nos enfocamos en los elementos de interés en t + 1. A
diferencia de la marginalización por filas, aquí no es necesario aplicar un escalamiento sobre la
TPM para mantener la coherencia probabilística.
■ Example 1.4 Partiendo de V = {A, B,C} se busca marginalizar en t manteniendo At+1 sobre la
TPM mostrada a continuación:

A 0 1 0 1 0 1 0 1
B 0 0 1 1 0 0 1 1 t +1
C 0 0 0 0 1 1 1 1
A
0
1
0
1
0
1
0
1

B
0
0
1
1
0
0
1
1
t

C
0
0
0
0
1
1
1
1

1
0
0
0
0
0
0
0

0
0
0
1
1
0
0
0

0
0
0
0
0
0
0
0

0
0
0
0
0
0
0
1

0
1
0
0
0
0
0
0

0
0
1
0
0
0
1
0

0
0
0
0
0
0
0
0

0
0
0
0
0
1
0
0


---
Capítulo 1. Planteamiento

12
Descartamos los elementos BCt+1 y resta realizar la agrupación de los estados en
At+1 . Es en este modo que la TPM se conoce como la representación Estado nodo,
posteriormente nos será de utilidad para realizar operaciones de descomposición y unión
entre las mismas.

A 0 1 t +1
A
0
1
0
1
0
1
0
1

B
0
0
1
1
0
0
1
1
t

C
0
0
0
0
1
1
1
1

1
1
0
0
0
0
0
0

0
0
1
1
1
1
1
1

■

En adición, se tiene relevancia de llevar la TPM a esta forma Estado nodo puesto es así que
se logra independencia causal de un nodo sobre el sistema, permitiéndose así realizar procesos de
marginalización sobre filas sin alguna alteración subyacente.
1.2.2

Probabilidad condicional
Al trabajar con una Matriz de Probabilidad de Transición (TPM) de tamaño n y con un estado
inicial conocido, podemos expresar la probabilidad de que el sistema esté en un determinado estado
en el tiempo t + 1 dado su estado en el tiempo t utilizando la notación:
p(ABCt+1 |ABCt = 100)
Es crucial entender que no existe interacción instantánea entre los elementos en un mismo tiempo t + i, donde i ∈ N. Esto implica que podemos calcular las probabilidades de forma independiente
para cada elemento en t + 1, dado el estado en t. Esta propiedad se conoce como independencia
condicional y se formula de la siguiente manera:
Theorem 1.2.1 — Independencia condicional.

p(AB · · · Zt+1 |AB · · · Zt ) = p(At+1 |AB · · · Zt ) · p(Bt+1 |AB · · · Zt ) · · · p(Zt+1 |AB · · · Zt )
Esta ecuación nos permite componer o descomponer la probabilidad conjunta en el producto
de las probabilidades individuales condicionales para un tiempo t + 1, facilitando así el análisis y
cálculo de las mismas.
■

Example 1.5

Consideremos un sistema con |V | = 3 elementos, y analicemos su representación en forma de
estado-nodo mediante las matrices A, B,C. Al aplicar la ecuación de independencia condicional
(1.2.1), podemos descomponer la matriz de transición completa (de la forma estado-estado) en el
producto tensorial de las matrices individuales:
(ABCt+1 |ABCt ) = (At+1 |ABCt ) ⊗ (Bt+1 |ABCt ) ⊗ (Ct+1 |ABCt )
Es el producto tensorial el operador que nos permite combinar las matrices individuales
manteniendo la coherencia de los estados y las probabilidades. A continuación, mostramos cómo
se realiza este proceso:


---
1.2 Conceptos

13
A 0 1 0 1 0 1 0 1
B 0 0 1 1 0 0 1 1 t +1
C 0 0 0 0 1 1 1 1
A
0
1
0
1
0
1
0
1

B
0
0
1
1
0
0
1
1
t

C
0
0
0
0
1
1
1
1

1
0
0
0
0
0
0
0

0
0
0
1
1
0
0
0

0
0
0
0
0
0
0
0

A 0 1 t +1
A
0
1
0
= 1
0
1
0
1

B
0
0
1
1
0
0
1
1
t

C
0
0
0
0
1
1
1
1

1
1
0
0
0
0
0
0

0
0
1
1
1
1
1
1

0
0
0
0
0
0
0
1

0
1
0
0
0
0
0
0

0
0
1
0
0
0
1
0

0
0
0
0
0
0
0
0

0
0
0
0
0
1
0
0

B 0 1 t +1
A
0
1
O 0
1
0
1
0
1

B
0
0
1
1
0
0
1
1
t

C
0
0
0
0
1
1
1
1

1
1
1
1
1
0
1
0

0
0
0
0
0
1
0
1

C 0 1 t +1
A
0
1
O 0
1
0
1
0
1

B
0
0
1
1
0
0
1
1
t

C
0
0
0
0
1
1
1
1

1
0
0
1
1
0
0
1

0
1
1
0
0
1
1
0

Definition 1.2.1

El producto tensorial es una operación que combina matrices de manera que el número de
filas se mantiene constante mientras que las columnas se multiplican. Si tenemos matrices M1 ∈
Rm×n1 y M2 ∈ Rm×n2 , entonces su producto tensorial es M3 = M1 ⊗ M2 , donde M3 ∈ Rm×(n1 ·n2 ) .
Es importante definir que esta operación es conmutativa, de forma que
1.
M1 (M2 ⊗ M3 ) = M2 (M3 ⊗ M1 ) = M3 (M1 ⊗ M2 )
2.
M1 ⊗ M2 ⊗ · · · ⊗ Mn = Mn ⊗ Mn−1 ⊗ · · · ⊗ M1
Es importante distinguir el producto tensorial del producto de Kronecker, que es otro tipo
de producto entre matrices. En el caso del producto de Kronecker, dado A ∈ Rm×n y B ∈ R p×q ,
el resultado es una matriz de tamaño mp × nq donde cada elemento de A se multiplica por la
matriz B completa.
Esto se aprecia en la siguiente generalización de dicho producto:


---
Capítulo 1. Planteamiento

14



a11 b11
 a11 b21

 ..
 .

 a11 b p1

 ..
 .
A⊗B = 
 ..
 .

am1 b11

am1 b21

 ..
 .
am1 b p1

a11 b12
a11 b22
..
.

···
···
..
.

a11 b p2 · · ·
..
.
..
.
am1 b12 · · ·
am1 b22 · · ·
..
..
.
.
am1 b p2 · · ·

a11 b1q
a11 b2q
..
.

···
...

···
···

a11 b pq · · ·
..
..
.
.
..
.
am1 b1q · · ·
am1 b2q · · ·
..
.

···

am1 b pq · · ·

···

..

.
···
···

···
...

a1n b11
a1n b21
..
.

a1n b12
a1n b22
..
.

a1n b p1
..
.
..
.
amn b11
amn b21
..
.

a1n b p2
..
.
..
.
amn b12 · · ·
amn b22 · · ·
..
..
.
.
amn b p2 · · ·

amn b p1

...
···


a1n b1q
a1n b2q 

.. 
. 

a1n b pq 

.. 
. 

..  .
. 

amn b1q 

amn b2q 

.. 
. 
amn b pq
■

1.2.3

Distancias Métricas
En matemáticas y ciencias de la computación la noción de distancia métrica se utiliza para
cuantificar cuán "lejanos" están dos puntos en un espacio determinado (espacio métrico). Una
métrica es una función que mide esta distancia, cumpliendo con propiedades esenciales como:
1. No negatividad: La distancia entre dos puntos siempre es mayor o igual que cero.
d(x, y) ≥ 0 ∧ d(x, y) = 0 ⇐⇒ x = y
2. Simetría: La distancia de un punto A a otro punto B es la misma que de B a A.
d(x, y) = d(y, x)
3. Desigualdad triangular: La distancia entre dos puntos A y C debe ser menor o igual a la
suma de las distancias entre A y B, y entre B y C, para cualquier tercer punto B.
d(x, z) ≤ d(x, y) + d(y, z)
Existen varias métricas que se utilizan en diferentes contextos, como la distancia Euclidiana y la
distancia Manhattan, pero una de las más relevantes en el análisis de datos y procesamiento de
imágenes y es la distancia Hamming utilizada en la Earth Mover’s Distance (EMD).
Earth Mover’s Distance

Una de los algoritmos más relevantes en el contexto de la comparación de distribuciones que
usan distancias métricas (ej. de probabilidad) es la EMD, también conocida como la distancia de
flujo óptimo. Esta métrica mide la mínima cantidad de "trabajo" (tierra) necesaria para transformar
una distribución (histograma, serie, etc...) en otra.
La EMD debe basarse en la solución de un problema de optimización conocido como el problema del transporte, donde dados dos conjuntos de datos A y B con sus distribuciones asociadas, la
EMD busca encontrar la forma de asignar elementos de A hacia los elementos de B, minimizando
el costo total de las asignaciones.
Definition 1.2.2 — Distancias métricas entre distribuciones de probabilidad.

Dadas dos distribuciones de probabilidad P1×2n , Q1×2n donde cada columna está indexada con
una cadena binaria en una notación particular (ej. Little Endian, Big Endian, Gray code, Sign
and magnitude, Two’s complement, etc...), el coste asociado no sólo depende la cantidad de
esfuerzo requerido desde la columna Pi hasta Q j obtenido con un movimiento por un algoritmo


---
1.2 Conceptos

15

de flujo (ej. EMD) sino que también por la diferencia entre objetos (índices binarios) de cada
distribución.
Formalmente el costo total g de mover una cantidad m entre dos posiciones i → j está
denotado por:
g(P, Q) = mín-mov(m) × d(i, j)
Theorem 1.2.2 — Distancia Hamming.

Es una de las más utilizadas para comparar secuencias binarias. Mide el número de posiciones
en las que dos cadenas x, y de igual longitud n tienen valores diferentes. Es ideal para medir
cuántos bits necesitan cambiar para transformar una cadena binaria en otra.
n

dHamming (x, y) = ∑ xi ⊕ yi
i=1


---

---
2. Bipartición

Con el fin de analizar si cada elemento del sistema influye en su evolución temporal, introducimos el concepto de k-partición. Este concepto implica que el sistema puede dividirse en k partes P
que son independientes entre sí para cualquier instante t + i, donde i ∈ N. En un sistema inicial V
con n elementos, el número de posibles k-particiones crece exponencialmente con el tamaño del
sistema, siguiendo un orden de Θ(k2n−1 − 1).
Para simplificar el análisis y hacerlo más manejable, nos enfocaremos en el caso de k = 2, es
decir, en biparticiones. Si consideramos u elementos en el tiempo t y v elementos en el tiempo t + 1,
el número de posibles biparticiones se calcula mediante:
Pk=2 (V ) = 2u+v−1 − 1
Esta fórmula nos muestra cómo el número de biparticiones posibles crece de forma exponencial
con respecto a la suma de los elementos en ambos tiempos.
■

Example 2.1 — Crecimiento exponencial.

Se puede apreciar el rápido crecimiento en la formación de biparticiones para un sistema con un
total de n = 2 elementos:
{0/ t+1 , 0/ t } ⊗ {ABt+1 , ABt };

{0/ t+1 , Bt } ⊗ {ABt+1 , At };

{0/ t+1 , At } ⊗ {ABt+1 , Bt };

{0/ t+1 , ABt } ⊗ {ABt+1 , 0/ t };

{Bt+1 , 0/ t } ⊗ {At+1 , ABt };

{Bt+1 , Bt } ⊗ {At+1 , At };

{Bt+1 , At } ⊗ {At+1 , Bt };

{Bt+1 , ABt } ⊗ {At+1 , 0/ t }.
■

2.1 Particionamiento
Es importante destacar que algunas particiones pueden ser triviales y no aportar información
adicional al análisis del sistema. Al considerar una bipartición, debemos entender que después de
aplicar el producto tensorial para recombinar las partes el sistema resultante puede o no comportarse
de manera idéntica al sistema original para ciertos estados iniciales.


---
Capítulo 2. Bipartición sistémica

18

Definition 2.1.1 No es posible comparar directamente una de las partes de la bipartición con el

sistema original. Solo después de unir las biparticiones mediante el producto tensorial podemos
comparar el sistema resultante con el original. Sin embargo, esta recombinación puede o no
introducir pérdida de información o variaciones en el comportamiento del sistema.
Es fundamental comprender que la única manera de obtener un sistema particionado es
a través del sistema original, aplicando las marginalizaciones necesarias para obtener los
subsistemas que luego serán recombinadas.
Es de esta forma que inicia la búsqueda por conocer cuál es la mejor forma de particionar el
sistema de forma tal que la pérdida generada entre este nuevo sistema particionado y el sistema
original sea mínima.
import numpy as np
from pyemd import emd
3 from numpy . typing import NDArray
1
2

4

def emd_pyphi ( u : NDArray [ np . float64 ] , v : NDArray [ np . float64 ]) -> float :
"""
7
Calculate the Earth Mover ’s Distance ( EMD ) between two probability
distributions u and v .
8
The Hamming distance was used as the ground metric .
9
"""
10
if not all ( isinstance ( arr , np . ndarray ) for arr in [u , v ]) :
11
raise TypeError ( " u and v must be numpy arrays . " )
5
6

12
13
14

n : int = len ( u )
costs : NDArray [ np . float64 ] = np . empty (( n , n ) )

15
16
17
18
19

for i in range ( n ) :
costs [i , : i ] = [ hamming_distance (i , j ) for j in range ( i ) ]
costs [: i , i ] = costs [i , : i ]
np . fill_diagonal ( costs , 0)

20
21
22

cost_matrix : NDArray [ np . float64 ] = np . array ( costs , dtype = np . float64 )
return emd (u , v , cost_matrix )

23
24
25

def hamming_distance ( a : int , b : int ) -> int :
return ( a ^ b ) . bit_count ()

Listing 2.1: Código Python con función EMD usando distancia Hamming


---
