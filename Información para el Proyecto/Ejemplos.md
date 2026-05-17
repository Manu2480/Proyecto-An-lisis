## Sheet: Hoja3

Ideas 
Se puede usar la partición de maxima modularidad (MMP) para calcular la información integrada, pues se busca calcular II  a través de la descomposcición más modular de una red neuronal
a la luz de trabajos anteriores que han demostrado que la información fluye a través de módulos relativamente discretos en el cerebro
We propose an alternative network partition acrosss which to calculate integrated information, whichis based on the graph-theoretic notion of modularity and bypasses the computational expense offinding the MIP and the artificiality of using the MIB. 
The modularity of a network quantifies theextent to which that network can be broken up into relatively discrete ”modules,” which are definedas densely interconnected communities of node
				Decomposing a neural network intoits ”Maximum Modularity Partition” (MMP) (Figure 1C) is therefore more congruent with what isknown about information flow in the brain than is calculating integrated information
				 across the MIB,because it is reflects the underlying functional architecture of neural networks. The MMP has thefurther advantage over the MIP and the MIB in being extremely quick to find

There are a number of ways of finding the MMP of a network. We utilized the Louvain Method fordetecting communities in graphs, which is a “greedy optimization” method and which seems to runon O(nlogn) time [25]

Para encontrar la MMP, primero obtenemos una matriz de adyacencia a partir de datos de series temporales. Específicamente, tomamos la autocorrelación de la serie temporal y binarizamos la matriz de correlación resultante en un umbral dado [37]. 
En este estudio, este umbral se fijó en una significancia estadística de alfa de 0,05 y en la mitad superior de la distribución de los valores absolutos de los coeficientes de correlación. Se cree que la matriz de adyacencia binaria resultante 
refleja la conectividad funcional de la red de la que se obtuvieron los datos de la serie temporal.
The adjacency matrix is then fed into the Louvain Algorithm, which iterates through different net-work partitions to maximize network modularity Q:
[25] Blondel VD, Guillaume JL, Lambiotte R, Lefebvre E. Fast unfolding of communities in largenetworks. Journal of statistical mechanics: theory and experiment. 2008;2008(10):P10008.
(12) (PDF) Moving Past the Minimum Information Partition: How To Quickly and Accurately Calculate Integrated Information. Available from: https://www.researchgate.net/publication/301895994_Moving_Past_the_Minimum_Information_Partition_How_To_Quickly_and_Accurately_Calculate_Integrated_Information [accessed Mar 20 2024].
Articulos con  herramientas para analisis de redes
[PDF] Exploring Network Structure, Dynamics, and Function using NetworkX | Semantic Scholar
METODO DEL GRAFO DE FLUJO DE RED
Se trata de encontrar la MIP de un sistema finito mediante la construcción de un grafo de flujo de red a partir de la tpm del sistema. El grafo se construye de tal manera que cada partición del sistema corresponde 
a una fuente y un destino en el grafo, y las aristas del grafo representan las transiciones entre estados. El algoritmo utiliza el flujo máximo en el grafo para encontrar la partición que maximiza la información integrada.
Como sería el grafo?
	-Cada estado del sistema se representa como un nodo en el grafo.
	-Para cada par de estados presentes y futuros (i, j), donde i y j son estados del sistema, se crea una arista dirigida del estado presente (i) al estado futuro (j) con peso igual a la probabilidad de transición de i a j en la TPM.
Como se asignarían los nodos fuente y destino?
Calcular flujo máximo
	Se utiliza un algoritmo de flujo máximo, como el algoritmo de Ford-Fulkerson o el algoritmo de Edmonds-Karp, para calcular el flujo máximo en el grafo.
	El flujo máximo representa la cantidad máxima de información que puede fluir desde la fuente hasta el destino sin exceder las capacidades de las aristas.

## Sheet: Formulas

		Observaciones:
		En los ejemplos nosostros asumimos una estructura de la red como se ha mostrado en las figuras, pero en general no se conoce la estructura subyacente. La perturbación y la observación 
		es lo que nos permite  a quienes experimentamos, determinar la TPM
		Condiciones de background: Como el objetivo es evaluar la informacion integrada de un sistema candidatos  cuando la red está en un estado en particular , entonces queremos determinar la TPM del sistema candidato
		 perturbándolo mientras los elementos externos están fijos en ese estado. A esos elementos externos fijados se les conoce como condiciones de background para el sistema candidato
		Mecanismos condicionalmente independientes 
		Matematicamente la independencia condicional se representa asi:
		lo que significa que dado el estado de un sistema en el tiempo t-1, la probabilidad de A, By C se puede calcular independientemente. Esto porque se supone que no hay interaccion instantanea entre 
		los mecanismos y además que las CAUSAS  deben preceder sus efectos. En nuestros modelos de sistemas físicos  descartamos la causación instantánea, esto se captura por el requerimiento
		 de que los elementos sean condicionalmente independientes. O sea que el estado de cada elemento en t+1 depende inicamente del estado del sistema en t y no de los estados de otros elementos  en t+1

		Una vez que se escoge un conjunto candidato, según IIT, los elementos por fuera de ese conjunto  son tratados como condiciones de background.
		Es decir, no se consideran como variables internas del conjunto sobre el que se hacen las perturbaciones, sino que se fijan sus valores y se tratan como condiciones externas.
		Esto significa que esas conexiones por fuera del sistema candidato no son ruidosas sino que se fijan  en sus valores actuales.

		Repertorio Causa-Efecto

		Recordemos que para calcular la información de causa-efecto de un mecanismo en un estado sobre un purview, se compara con el repertorio PUC sin restricciones.  mecanismo en un estado sobre un ámbito se evalúa comparando su repertorio de causa-efecto con el de el ámbito particionado. La forma en que se derivan estas distribuciones de probabilidad se ilustra utilizando el ejemplo del mecanismo A = 1 en el ámbito ABC de la Fig. 4 (texto principal), así como otros mecanismos del conjunto candidato ABC (Fig. 1, texto principal).
		 La información integrada de un mecanismo en un estado sobre un ámbito se evalúa comparando su repertorio de causa-efecto con el de 
		purview particionado.
		Repertorio EFECTO
		El repertorio efecto 										se calcula fijando el estado actual de A en 1, mientras los elementos restantes B y C son independientemente
		 perturbadas en todos sus posibles estados con igual probabilidad
		Otra vez, las entradas comunes de B o C pueden llevar a correlaciones entre																		y	Se usan elementos virtualespara reemplazar los elementos B y C 
		con salidas independientes a todos los elementos y asi evitar contar estas correlaciones como efectos de elementos.
		Como todos los mecanismos  bajo consideración son condicionalmente independientes, en la práctica el repertorio efecto  puede calcularse así:
		esto significa que el repertorio efecto de un solo elemento en el futuro, por ejemplo 																	 		es simplemente:
		PyPHI: Toolbox for integration information
		Cause-effect structures (system-level information).
		The next step is to compute the CES, the set of all concepts specified by the subsystem. The CES characterizes all of the causal constraints that are intrinsic to a physical system. This is implemented by the pyphi.compute.ces() function, which simply calls Subsystem.concept() for every mechanism 
		, where 
		 is the power set of subsystem nodes. It returns a CauseEffectStructure object containing those Concepts for which φ > 0.
		We see that every mechanism in 
		 except for AC specifies a concept, as described in Fig. 10 of [3]:

		Irreducible cause-effect structures (system-level integration).
		At this point, the irreducibility of the subsystem’s CES is evaluated by applying the integration postulate at the system level. As with integration at the mechanism level, the idea is to measure the difference made by each partition and then take the minimal value as the irreducibility of the subsystem.
		We begin by performing a system cut. Graphically, the subsystem is partitioned into two parts and the edges going from one part to the other are cut, rendering them causally ineffective. This is implemented as an operation on the TPM as follows: Let Ecut denote the set of directed edges in the subsystem that are to be cut, where each edge e ∈ Ecut has a source node a and a target node b. For each edge, we modify the individual TPM of node b (Fig 2) by marginalizing over the states of a at t. The resulting TPM specifies the function implemented by b with the causal influence of a removed. We then combine the modified node TPMs to recover the full TPM of the partitioned subsystem. Finally, we recalculate the CES of the subsystem with this modified TPM (the partitioned CES).
		The irreducibility of a CES with respect to a partition is the distance between the unpartitioned and partitioned CESs (calculated with pyphi.compute.ces_distance(); several distances are supported; see § Configuration). This distance is evaluated for every partition, and the minimum value across all partitions is the subsystem’s integrated information Φ, which measures the extent to which the CES specified by the subsystem is irreducible to the CES under the minimal partition.
		This procedure is implemented by the pyphi.compute.sia() function, which returns a SystemIrreducibilityAnalysis object (Fig 1). We can verify that the Φ value of the example system in [3] is 1.92 and the minimal partition is that which removes the causal connections from AB to C:

## Sheet: Ej1RepEfectSinEV

Calculo Repertorio Efecto  ejemplo
Ahora vamos a  calcular el repertorio efecto con elementos virtuales, ahora lo haremos sin elementos virtuales teniendo en cuenta lo xplicado en la hoja  RepEfectoConEV 
tomando como referencia la siguiente formula:
lo que significa que dado el estado de un sistema en el tiempo t-1, la probabilidad de A, By C se puede calcular independientemente. Esto porque se supone que no hay interaccion instantanea entre 
los mecanismos y además que las CAUSAS  deben preceder sus efectos.
Una vez que se escoge un conjunto candidato, según IIT, los elementos por fuera de ese conjunto  son tratados como condiciones de background.
Es decir, no se consideran como variables internas del conjunto sobre el que se hacen las perturbaciones, sino que se fijan sus valores y se tratan como condiciones externas.
Esto significa que esas conexiones por fuera del sistema candidato no son ruidosas sino que se fijan  en sus valores actuales.
Estado actual :   A B C		1 0 0

Como todos los mecanismos  bajo consideración son condicionalmente independientes, en la práctica el repertorio efecto  puede calcularse así:
Esto significa que el repertorio efecto de un solo elemento en el futuro, por ejemplo 													es simplemente:
Partimos de la TPM 
		estado futuro	A	0	1	0	1	0	1	0	1
			B	0	0	1	1	0	0	1	1
Estado actual			C	0	0	0	0	1	1	1	1
A	B	C
0	0	0		1	0	0	0	0	0	0	0
1	0	0		0	0	0	0	1	0	0	0
0	1	0		0	0	0	0	0	1	0	0
1	1	0		0	1	0	0	0	0	0	0
0	0	1		0	1	0	0	0	0	0	0
1	0	1		0	0	0	0	0	0	0	1
0	1	1		0	0	0	0	0	1	0	0
1	1	1		0	0	0	1	0	0	0	0
Lo que queremos  es calcular 						, y según lo mencionado anteriormente, debemos calcular:
1)
2)									      y    
3)
1) Vamos  a empezar por la primera:
Lo primero que vamos a hacer es marginalizar los elementos del no-purview, es decir, ignorar los elementos por  fuera del purview, en este caso B, C, y 
marginalizarlos de la TPM y se tratan como si fueran condiciones de background . Empezamos por eliminar  B del purview y la TPM quedaría así:
												OJO --------->	luego sumamos pares de columnas cuyos estados solo diferían por 
													 el estado de B y  no se normaliza(o sea  no dividimos entre 2) yqueda asi: 
		estado futuro
			A	0	1	0	1	0	1	0	1				E. futuro	A	0	1	0	1
Estado actual			C	0	0	0	0	1	1	1	1		E. Actual			C	0	0	1	1
A	B	C											A	B	C
0	0	0		1	0	0	0	0	0	0	0		0	0	0		1	0	0	0
1	0	0		0	0	0	0	1	0	0	0		1	0	0		0	0	1	0
0	1	0		0	0	0	0	0	1	0	0		0	1	0		0	0	0	1
1	1	0		0	1	0	0	0	0	0	0		1	1	0		0	1	0	0
0	0	1		0	1	0	0	0	0	0	0		0	0	1		0	1	0	0
1	0	1		0	0	0	0	0	0	0	1		1	0	1		0	0	0	1
0	1	1		0	0	0	0	0	1	0	0		0	1	1		0	0	0	1
1	1	1		0	0	0	1	0	0	0	0		1	1	1		0	1	0	0
Luego marginalizamos sobre C, es decir eliminamos C del purview  igual que como se hizo con B y la TPM quedaría asi:
como si fuese una condicion de background
		E. futuro
E. Actual			A	0	1	0	1						A	0	1
A	B	C								A	B	C
0	0	0		1	0	0	0			0	0	0		1	0
1	0	0		0	0	1	0			1	0	0		1	0
0	1	0		0	0	0	1			0	1	0		0	1
1	1	0		0	1	0	0			1	1	0		0	1
0	0	1		0	1	0	0			0	0	1		0	1
1	0	1		0	0	0	1			1	0	1		0	1
0	1	1		0	0	0	1			0	1	1		0	1
1	1	1		0	1	0	0			1	1	1		0	1
Ahora en el siguiente paso empezaremos a marginalizar sobre los elementos del no-mecanismo , en este caso B y C. 
Empezamos primero marginalizando por B.
		A	0	1			Aquí se debe normalizar (se divide por 2)
A	C
0	0		1	0					A	0	1
1	0		1	0			A	C
0	0		0	1			0	0		0.5	0.5
1	0		0	1	 		1	0		0.5	0.5
0	1		0	1			0	1		0	1
1	1		0	1			1	1		0	1
0	1		0	1
1	1		0	1
Ahora marginalizamos el mecanismo sobre C
							Aquí se debe normalizar (se divide por 2)
	A	0	1
A							A	0	1					A	0	1
0		0.5	0.5			A							A
1		0.5	0.5			0		0.25	0.75				1		0.25	0.75
0		0	1			1		0.25	0.75
1		0	1									Se selecciona este, porque  A
												 en el estado actual aparece en 1
2) Ahora vamos a continuar con  la siguiente:
Lo primero que vamos a hacer es marginalizar los elementos del no-purview, es decir, ignorar los elementos por  fuera del purview, en este caso A, C, y 
marginalizarlos de la TPM y se tratan como si fueran condiciones de background . Empezamos por eliminar  A del purview y la TPM quedaría así:
													OJO --------->	luego sumamos pares de columnas cuyos estados solo diferían por 
		estado futuro												 el estado de A y  no se normaliza(o sea  no dividimos entre 2) yqueda asi: 
			B	0	0	1	1	0	0	1	1					E. futuro	B	0	1	0	1
Estado actual			C	0	0	0	0	1	1	1	1			E. Actual			C	0	0	1	1
A	B	C												A	B	C
0	0	0		1	0	0	0	0	0	0	0			0	0	0		1	0	0	0
1	0	0		0	0	0	0	1	0	0	0			1	0	0		0	0	1	0
0	1	0		0	0	0	0	0	1	0	0			0	1	0		0	0	1	0
1	1	0		0	1	0	0	0	0	0	0			1	1	0		1	0	0	0
0	0	1		0	1	0	0	0	0	0	0			0	0	1		1	0	0	0
1	0	1		0	0	0	0	0	0	0	1			1	0	1		0	0	0	1
0	1	1		0	0	0	0	0	1	0	0			0	1	1		0	0	1	0
1	1	1		0	0	0	1	0	0	0	0			1	1	1		0	1	0	0
Luego marginalizamos sobre C, es decir eliminamos C del purview  igual que como se marginalizo  A y la TPM quedaría asi:
como si fuese una condicion de background
											luego sumamos pares de columnas cuyos estados solo diferían por 
											 el estado de C y  no se normaliza(o sea  no dividimos entre 2) yqueda asi: 
		E. Futuro											E. Futuro
E.Actual			B	0	1	0	1				E.Actual			B	0	1
A	B	C									A	B	C
0	0	0		1	0	0	0				0	0	0		1	0
1	0	0		0	0	1	0				1	0	0		1	0
0	1	0		0	0	1	0				0	1	0		1	0
1	1	0		1	0	0	0				1	1	0		1	0
0	0	1		1	0	0	0				0	0	1		1	0
1	0	1		0	0	0	1				1	0	1		0	1
0	1	1		0	0	1	0				0	1	1		1	0
1	1	1		0	1	0	0				1	1	1		0	1
Ahora en el siguiente paso empezaremos a marginalizar sobre los elementos del no-mecanismo , en este caso B y C. 
Empezamos primero marginalizando por B.
		B	0	1			Aquí se debe normalizar (se divide por 2)
A	C
0	0		1	0					B	0	1
1	0		1	0			A	C
0	0		1	0			0	0		1	0
1	0		1	0	 		1	0		1	0
0	1		1	0			0	1		1	0
1	1		0	1			1	1		0	1
0	1		1	0
1	1		0	1
Ahora marginalizamos el mecanismo sobre C
							Aquí se debe normalizar (se divide por 2)
	B	0	0
A							B	0	1					B	0	1
0		1	0			A							A
1		1	0			0		1	0				1		0.5	0.5
0		1	0			1		0.5	0.5
1		0	1									Se selecciona este, porque  A
												 en el estado actula aparece en 1
3)  Ahora vamos a continuar con  la siguiente:
Lo primero que vamos a hacer es marginalizar los elementos del no-purview, es decir, ignorar los elementos por  fuera del purview,
 en este caso A, B y  marginalizarlos de la TPM y se tratan como si fueran condiciones de background . Empezamos por eliminar  A del purview 
y la TPM quedaría así:
													OJO --------->	luego sumamos pares de columnas cuyos estados solo diferían por 
		estado futuro												 el estado de A y  no se normaliza(o sea  no dividimos entre 2) yqueda asi: 
			B	0	0	1	1	0	0	1	1					E. futuro	B	0	1	0	1
Estado actual			C	0	0	0	0	1	1	1	1			E. Actual			C	0	0	1	1
A	B	C												A	B	C
0	0	0		1	0	0	0	0	0	0	0			0	0	0		1	0	0	0					En este caso, se estaría iniciando igual que en la etapa anterior, por ende  haciendo exactamente el mismo cálculo
1	0	0		0	0	0	0	1	0	0	0			1	0	0		0	0	1	0
0	1	0		0	0	0	0	0	1	0	0			0	1	0		0	0	1	0
1	1	0		0	1	0	0	0	0	0	0			1	1	0		1	0	0	0
0	0	1		0	1	0	0	0	0	0	0			0	0	1		1	0	0	0
1	0	1		0	0	0	0	0	0	0	1			1	0	1		0	0	0	1
0	1	1		0	0	0	0	0	1	0	0			0	1	1		0	0	1	0
1	1	1		0	0	0	1	0	0	0	0			1	1	1		0	1	0	0
Luego marginalizamos sobre B, es decir eliminamos B del purview  igual que como se marginalizo  A
como si fuese una condicion de background,  y la TPM quedaría asi:
											luego sumamos pares de columnas cuyos estados solo diferían por 
											 el estado de B y  no se normaliza(o sea  no dividimos entre 2) yqueda asi: 
		E. futuro										E. futuro
E. Actual			C	0	0	1	1			E. Actual			C	0	1
A	B	C								A	B	C
0	0	0		1	0	0	0			0	0	0		1	0
1	0	0		0	0	1	0			1	0	0		0	1
0	1	0		0	0	1	0			0	1	0		0	1
1	1	0		1	0	0	0			1	1	0		1	0
0	0	1		1	0	0	0			0	0	1		1	0
1	0	1		0	0	0	1			1	0	1		0	1
0	1	1		0	0	1	0			0	1	1		0	1
1	1	1		0	1	0	0			1	1	1		1	0
Ahora en el siguiente paso empezaremos a marginalizar sobre los elementos del no-mecanismo , en este caso B y C. 
Empezamos primero marginalizando por B (en el mecanismo).
	E. futuro
E. Actual		C	0	1			Aquí se debe normalizar (se divide por 2)
A	C
0	0		1	0					C	0	1
1	0		0	1			A	C
0	0		0	1			0	0		0.5	0.5
1	0		1	0			1	0		0.5	0.5
0	1		1	0			0	1		0.5	0.5
1	1		0	1			1	1		0.5	0.5
0	1		0	1
1	1		1	0
Ahora marginalizamos el mecanismo sobre C
							Aquí se debe normalizar (se divide por 2)
	C	0	1
A							C	0	1					C	0	1
0		0.5	0.5			A							A
1		0.5	0.5			0		0.5	0.5				1		0.5	0.5
0		0.5	0.5			1		0.5	0.5
1		0.5	0.5									Se selecciona este, porque  A
												 en el estado actula aparece en 1
Una vez ya calculados independientemente cada elemento del purview, en la siguiente etapa se hace el producto tensor asi: 
 
lo que sigue es hacer el producto tensor sobre los resultados de cada  factor que se obtuvieron previamente. El producto queda asi:
						Estado futuro						Estado futuro						Estado futuro
						A	0	1				B	0	1				C	0	1
					A						A						A
					1		0.25	0.75			1		0.5	0.5			1		0.5	0.5
					0		0.25	0.75			0		1	0			0		0.5	0.5
								Estado futuro									Estado futuro
								A	0	0	1	1
								B	0	1	0	1					C	0	1
							A									A
							1		0.125	0.125	0.375	0.375				1		0.5	0.5
									0.25	0	0.75	0						0.5	0.5
									Estado futuro
									A	0	0	0	0	1	1	1	1
									B	0	0	1	1	0	0	1	1
									C	0	1	0	1	0	1	0	1
								A
								1		0.0625	0.0625	0.0625	0.0625	0.1875	0.1875	0.1875	0.1875
								0		0.125	0.125	0	0	0.375	0.375	0	0
										0.09375	0.09375	0.03125	0.03125	0.28125	0.28125	0.09375	0.09375

## Sheet: RepEfectoUC

	REPERTORIO EFECTO NO RESTRINGIDO (UC unconstrained)
	Para calcular la información efecto (ei) también necesitamos calcular  la distribución futura o repertorio futuro no restringido 
															Nota: Cuando por ejemplo, hacemos una partición y una de las partes es (BF|ØC)
			Estado Futuro	A	0	1	0	1	0	1	0	1			calcular  P(BF|ØC) es lo mismo que calcular el repertorio  NO restringido de B
				B	0	0	1	1	0	0	1	1
	Estado Actual			C	0	0	0	0	1	1	1	1
	A	B	C
	0	0	0		1	0	0	0	0	0	0	0
	1	0	0		0	0	0	0	1	0	0	0
	0	1	0		0	0	0	0	0	1	0	0
	1	1	0		0	1	0	0	0	0	0	0
	0	0	1		0	1	0	0	0	0	0	0
	1	0	1		0	0	0	0	0	0	0	1
	0	1	1		0	0	0	0	0	1	0	0
	1	1	1		0	0	0	1	0	0	0	0
	Sin ninguna restricción de un mecanismo en un estado , el repertorio efecto no restringido  																        esta dado por:
	donde los elementos virtuales son usados para evitar incluir efectos  de las correlaciones  debido a las entradas comunes.
	En la práctica, los cálculos pueden hacerse de forma más sencilla de lo descrito hasta ahora.
	• Un truco que podemos usar para simplificar las cosas surge del hecho de que en nuestro modelo de sistemas físicos
	descartamos la causalidad instantánea
	• Esto se refleja en el requisito de que los elementos sean condicionalmente independientes.
	• Es decir, el estado de cada elemento en t+ 1 depende sólo del estado del sistema en t  y no de los estados de otros elementos en t+1
	• La independencia condicional implica que si p es una distribución sobre los estados de un elemento X y q es la distribución sobre los estados de Y, entonces la distribución conjunta de X e Y es el producto pq
	• Entonces, cuando calculamos un repertorio de efectos sobre algún purview, podemos simplemente tomar el producto de los repertorios de efectos individuales de todos los elementos del purview.
	• Esto también se aplica a los repertorios de causas, aunque en ese caso los repertorios son sobre los elementos individuales del mecanismo.
	• De esta manera, solo necesitamos calcular el repertorio efecto sobre purviews de un solo elemento, asi no podría haber entradas comunes y
	en conclusion, no hay necesidad de implementar elementos virtuales
	Por tanto para mecanismos independientes condicionalmente, esto seria lo mismo que:
	el producto de las distribuciones de probabilidad efecto  de cada elemento  dadas las entradas no restringidas
	como se muestra a continuación:
	Aquí se tiene la matriz con todos los posibles estados actuales para mirar  la probabilidad de A en el futuro. Mas adelante se hace lo mismo con B y con C

		Estado presente			Estado Futuro
		A	B	C	P(A=1)
		0	0	0	0			B	C	P(A=1)
		1	0	0	0			0	0	0		P(A=0)	P(A=1)
		0	1	0	1			1	0	1		0.25	0.75
		1	1	0	1			0	1	1
		0	0	1	1			1	1	1
		1	0	1	1			Esto no es necesrio
		0	1	1	1
		1	1	1	1
		Estado presente			Estado Futuro
		A	B	C	P(B=1)
		0	0	0	0			A	C	P(B=1)														A	0	0	0	0	1	1	1	1
		1	0	0	0			0	0	0		P(B=0)	P(B=1)		P(A=0)	P(A=1)		P(B=0)	P(B=1)		P(C=0)	P(C=1)		B	0	0	1	1	0	0	1	1
		0	1	0	0			1	0	0		0.75	0.25		0.25	0.75		0.75	0.25		0.5	0.5		C	0	1	0	1	0	1	0	1
		1	1	0	0			0	1	0																0.09375	0.03125	0.03125	0.28125	0.28125	0.09375	0.09375
		0	0	1	0			1	1	1						0	1	0	1						0,09375*2		0,03125*2		0,28125 *2		0,09375*2
		1	0	1	1			Esto no es necesario								0	0	1	1
		0	1	1	0											0.125	0.375	0.125	0.375
		1	1	1	1
		Estado presente			Estado Futuro
		A	B	C	P(C=1)
		0	0	0	0
		1	0	0	1			A	B	P(C=1)
		0	1	0	1			0	0	0		P(C=0)	P(C=1)
		1	1	0	0			1	0	1		0.5	0.5											C	0	0	0	0	1	1	1	1
		0	0	1	0			0	1	1														B	0	0	1	1	0	0	1	1	Esta es la misma solo que en la convencion little endian
		1	0	1	1			1	1	0														A	0	1	0	1	0	1	0	1
		0	1	1	1																				0,09375*2	0.28125	0.03125	0.09375	0.09375	0.28125	0.03	0.09
		1	1	1	0

## Sheet: Ej2RepEfectoSinEV

											estado futuro	A	0	1	0	1	0	1	0	1
												B	0	0	1	1	0	0	1	1
									Estado actual			C	0	0	0	0	1	1	1	1
									A	B	C
									0	0	0		1	0	0	0	0	0	0	0
									1	0	0		0	0	0	0	1	0	0	0
									0	1	0		0	0	0	0	0	1	0	0
									1	1	0		0	1	0	0	0	0	0	0
									0	0	1		0	1	0	0	0	0	0	0
									1	0	1		0	0	0	0	0	0	0	1
									0	1	1		0	0	0	0	0	1	0	0
									1	1	1		0	0	0	1	0	0	0	0
Vamos a hacer el cálculo del repertorio efecto para este ejemplo. 
Empezaremos haciendo el cálculo sin usar elementos virtuales y tomaremos como referencia la siguiente formula
lo que significa que dado el estado de un sistema en el tiempo t-1, la probabilidad de A, By C se puede calcular independientemente. Esto porque se supone que no hay interaccion instantanea entre 
los mecanismos y además que las CAUSAS  deben preceder sus efectos.
En nuestro ejemplo trabajaremos  el mecanismo C sobre el purview  B,C; con lo que nuestra formula seria asi:
Esto require calcular:
1)						y
2)
Empezamos calculando 1)
En este  paso marginalizamos sobre el purview B (marginalizando los elementos que no hacen parte del purview o sea AyC)
		estado futuro	Marginalizamos sobre A (purview)																					Marginalzamos sobre C
			B	0	0	1	1	0	0	1	1						E. futuro	B	0	1	0	1				E. futuro
Estado actual			C	0	0	0	0	1	1	1	1				E. Actual			C	0	0	1	1		E. Actual			B	0	1
A	B	C													A	B	C							A	B	C
0	0	0		1	0	0	0	0	0	0	0				0	0	0		1	0	0	0		0	0	0		1	0
1	0	0		0	0	0	0	1	0	0	0				1	0	0		0	0	1	0		1	0	0		1	0
0	1	0		0	0	0	0	0	1	0	0				0	1	0		0	0	1	0		0	1	0		1	0
1	1	0		0	1	0	0	0	0	0	0				1	1	0		1	0	0	0		1	1	0		1	0
0	0	1		0	1	0	0	0	0	0	0				0	0	1		1	0	0	0		0	0	1		1	0
1	0	1		0	0	0	0	0	0	0	1				1	0	1		0	0	0	1		1	0	1		0	1
0	1	1		0	0	0	0	0	1	0	0				0	1	1		0	0	1	0		0	1	1		1	0
1	1	1		0	0	0	1	0	0	0	0				1	1	1		0	1	0	0		1	1	1		0	1
Aquí empezamos a marginalizar sobre el mecanismo C (quitando los elementos que no hacen parte del mecanismo o sea Ay B
Marginalizamos sobre A:															Marginalizamos sobre B
	E. futuro						E. futuro								E. futuro								E. futuro
Estado actual		B	0	1		E. actual		B	0	1						B	0	1						B	0	1
B	C					B	C							E. actual	C							E. actual	C
0	0		1	0		0	0		1	0					0		1	0					0		1	0
0	0		1	0		1	0		1	0					0		1	0					1		0.5	0.5
1	0		1	0		0	1		0.5	0.5					1		0.5	0.5
1	0		1	0		1	1		0.5	0.5					1		0.5	0.5
0	1		1	0
0	1		0	1
1	1		1	0
1	1		0	1
Vamos a calcular 2)
En este  paso marginalizamos sobre el purview C (marginalizando los elementos que no hacen parte del purview o sea Ay B)
		estado futuro	Primero marginalizamos sobre A (purview)																					Marginalizamos luego sobre B
			B	0	0	1	1	0	0	1	1						E. futuro	B	0	1	0	1				E. futuro
Estado actual			C	0	0	0	0	1	1	1	1				E. Actual			C	0	0	1	1		E. Actual			C	0	1
A	B	C													A	B	C							A	B	C
0	0	0		1	0	0	0	0	0	0	0				0	0	0		1	0	0	0		0	0	0		1	0
1	0	0		0	0	0	0	1	0	0	0				1	0	0		0	0	1	0		1	0	0		0	1
0	1	0		0	0	0	0	0	1	0	0				0	1	0		0	0	1	0		0	1	0		0	1
1	1	0		0	1	0	0	0	0	0	0				1	1	0		1	0	0	0		1	1	0		1	0
0	0	1		0	1	0	0	0	0	0	0				0	0	1		1	0	0	0		0	0	1		1	0
1	0	1		0	0	0	0	0	0	0	1				1	0	1		0	0	0	1		1	0	1		0	1
0	1	1		0	0	0	0	0	1	0	0				0	1	1		0	0	1	0		0	1	1		0	1
1	1	1		0	0	0	1	0	0	0	0				1	1	1		0	1	0	0		1	1	1		1	0
Aquí empezamos a marginalizar sobre el mecanismo C (quitando los elementos que no hacen parte del mecanismo o sea Ay B
Marginalizamos sobre A:																Marginalizamos sobre B
																E. futuro								E. futuro
	E. futuro							E. futuro									C	0	1						C	0	1
		C	0	1			E. actual		C	0	1				E. actual	C							E. actual	C
B	C						B	C								0		0.5	0.5					0		0.5	0.5
0	0		1	0			0	0		0.5	0.5					0		0.5	0.5					1		0.5	0.5
0	0		0	1			1	0		0.5	0.5					1		0.5	0.5
1	0		0	1			0	1		0.5	0.5					1		0.5	0.5
1	0		1	0			1	1		0.5	0.5
0	1		1	0
0	1		0	1
1	1		0	1
1	1		1	0
Una vez claculado 1) y 2) procedemos a plicar el producto Tensor
								Estado futuro						Estado futuro
								B	0	1				C	0	1
							C						C
							0		1	0			0		0.5	0.5
										Estado futuro
										B	0	0	1	1
										C	0	1	0	1
									C
									0		0.5	0.5	0	0
							Estado futuro

## Sheet: EjParticion

Vamos a desarrollar el siguiente ejemplo completo con el fin de hacer las particiones.
Tenemos la TPM base del sistema
			estado futuro	A	0	1	0	1	0	1	0	1
				B	0	0	1	1	0	0	1	1
	Estado actual			C	0	0	0	0	1	1	1	1
	A	B	C
	0	0	0		1	0	0	0	0	0	0	0
	1	0	0		0	0	0	0	1	0	0	0
	0	1	0		0	0	0	0	0	1	0	0
	1	1	0		0	1	0	0	0	0	0	0
	0	0	1		0	1	0	0	0	0	0	0
	1	0	1		0	0	0	0	0	0	0	1
	0	1	1		0	0	0	0	0	1	0	0
	1	1	1		0	0	0	1	0	0	0	0
Este es el mecanismo AC sobre el purview ABC
													Este problema podemos representarlo asi:
1)Hallamos la distribución de probabilidadess para el sistema en el estado inicial A=1 C=0, porque B no hace parte de lo que queremos revisar.
En este orden de ideas,  según la fórmula definida previamente  calcularemos cada parte y luego aplicaremos el producto tensor. consiguiente 
Debemos calcular:
1)
2) 
3)
Empezando por  1) se tiene:
Debemos marginalizar sobre el purview en B y C, obteniendo:
																		Luego se marginaliza sobre el mecanismo
		E. futuro	A	0	1	0	1
E. Actual			C	0	0	1	1							A	0	1
A	B	C									A	B	C							A	0	1			Aquí se debe normalizar (se divide por 2)
0	0	0		1	0	0	0				0	0	0		1	0		A	C
1	0	0		0	0	1	0				1	0	0		1	0		0	0		1	0					A	0	1
0	1	0		0	0	0	1				0	1	0		0	1		1	0		1	0			A	C
1	1	0		0	1	0	0				1	1	0		0	1		0	0		0	1			0	0		0.5	0.5		   
0	0	1		0	1	0	0				0	0	1		0	1		1	0		0	1	 		1	0		0.5	0.5
1	0	1		0	0	0	1				1	0	1		0	1		0	1		0	1			0	1		0	1
0	1	1		0	0	0	1				0	1	1		0	1		1	1		0	1			1	1		0	1
1	1	1		0	1	0	0				1	1	1		0	1		0	1		0	1
				0.125	0.375	0.125	0.375								0.25	0.75		1	1		0	1
Ahora seguimos con 2)
Debemos marginalizar sobre el purview en A y C
luego sumamos pares de columnas cuyos estados solo diferían por 														luego sumamos pares de columnas cuyos estados 
 el estado de A y  no se normaliza(o sea  no dividimos entre 2) yqueda asi: 														 solo diferían por  el estado de C y  no se normaliza
			B	0	1	0	1							(o sea  no dividimos entre 2) yqueda asi: 
Estado actual			C	0	0	1	1									E. Futuro
A	B	C												E.Actual			B	0	1				Luego se marginaliza sobre el mecanismo
0	0	0		1	0	0	0							A	B	C									B	0	1			Aquí se debe normalizar (se divide por 2)
1	0	0		0	0	1	0							0	0	0		1	0				A	C
0	1	0		0	0	1	0							1	0	0		1	0				0	0		1	0					B	0	1
1	1	0		1	0	0	0							0	1	0		1	0				1	0		1	0			A	C
0	0	1		1	0	0	0							1	1	0		1	0				0	0		1	0			0	0		1	0
1	0	1		0	0	0	1							0	0	1		1	0				1	0		1	0		 	1	0		1	0
0	1	1		0	0	1	0							1	0	1		0	1				0	1		1	0			0	1		1	0
1	1	1		0	1	0	0							0	1	1		1	0				1	1		0	1			1	1		0	1
														1	1	1		0	1				0	1		1	0
																							1	1		0	1
Luego seguimo con 3)
Debemos marginalizar sobre el purview en A y B
luego sumamos pares de columnas cuyos estados solo diferían por 
 el estado de A y  no se normaliza(o sea  no dividimos entre 2) yqueda asi: 														luego sumamos pares de columnas cuyos estados 
		E. futuro	B	0	1	0	1							 solo diferían por  el estado de B y  no se normaliza
E. Actual			C	0	0	1	1							(o sea  no dividimos entre 2) yqueda asi: 
A	B	C														E. futuro						Luego se marginaliza sobre el mecanismo
0	0	0		1	0	0	0							E. Actual			C	0	1				E. futuro
1	0	0		0	0	1	0							A	B	C						E. Actual		C	0	1			Aquí se debe normalizar (se divide por 2)
0	1	0		0	0	1	0							0	0	0		1	0			A	C
1	1	0		1	0	0	0							1	0	0		0	1			0	0		1	0					C	0	1
0	0	1		1	0	0	0							0	1	0		0	1			1	0		0	1			A	C
1	0	1		0	0	0	1							1	1	0		1	0			0	0		0	1			0	0		0.5	0.5
0	1	1		0	0	1	0							0	0	1		1	0			1	0		1	0			1	0		0.5	0.5
1	1	1		0	1	0	0							1	0	1		0	1			0	1		1	0			0	1		0.5	0.5
														0	1	1		0	1			1	1		0	1			1	1		0.5	0.5
														1	1	1		1	0			0	1		0	1
																						1	1		1	0
												A	0	1					B	0	1					C	0	1
										A	C						A	C						A	C

										1	0		0.5	0.5			1	0		1	0			1	0		0.5	0.5

														A	0	0	0	0	1	1	1	1
														B	0	0	1	1	0	0	1	1												SISTEMA SIN DESCOMPONER
														C	0	1	0	1	0	1	0	1
												A	C
												1	0		0.25	0.25	0	0	0.25	0.25	0	0
2) Ahora se hace la descomposcion del sistema en dos partes: 															y
     ⇒ que debemos calcular:
       a)
				 y
         b)
- Empezamos por  a)
⇒
Para este hacemos todo el procedimiento co mo se ha explicado anteriormente. 
Primero trabajamos sobre los efectos futuros en A, lo que implica marginalizar a B y C
			estado futuro	A	0	1
	Estado actual											Luego nos interesa el estado actual (mecanismo) en AC entonces marginalizamos sobre B (hay que dividir entre 2)
	A	B	C									A	0	1																⇒
	0	0	0		1	0				A	C
	1	0	0		1	0				0	0		0.5	0.5
	0	1	0		0	1				1	0		0.5	0.5
	1	1	0		0	1				0	1		0	1
	0	0	1		0	1				1	1		0	1
	1	0	1		0	1
	0	1	1		0	1
	1	1	1		0	1
Ahora calculamos 
Para este hacemos todo el procedimiento co mo se ha explicado anteriormente. 
Primero trabajamos sobre los efectos futuros en B, lo que implica marginalizar a A y C
	Estado actual		E.futuro	B	0	1
	A	B	C
	0	0	0		1	0				Luego nos interesa el estado actual (mecanismo) en AC entonces marginalizamos sobre B (no olvidar dividir entre 2)
	1	0	0		1	0						B	0	1
	0	1	0		1	0				A	C
	1	1	0		1	0				0	0		1	0
	0	0	1		1	0				1	0		1	0
	1	0	1		0	1				0	1		1	0
	0	1	1		1	0				1	1		0	1
	1	1	1		0	1
					0.75	0.25
En este punto tenemos:
																										A	0	1	0	1
												A	0	1					B	0	1					B	0	0	1	1
										A	C						A	C						A	C
										1	0		0.5	0.5			1	0		1	0			1	0		0.5	0.5	0	0
- Luego calculamos b)						En este caso esta es la distribución no restringida sobre los estados próximos (futuros) de C.
						Entonces en este caso no se marginaliza   sobre las filas, ya que no se restringen los valores, porque no hay 
				     ⇒		un estado definido en el tiempo presente. Dada esta situación lo que hacemos es calcular la probabilidad de  C=0
						y para eso nos ubicamos en la columno donde C=0 y sumamos todos los valores en todos los estados (filas) y se divide 
						por la cantidad total de estados. Despues hacemos el mismo procedimiento pero para C=1
			E. futuro
	E. Actual			C	0	1
	A	B	C
	0	0	0		1	0
	1	0	0		0	1
	0	1	0		0	1										C	0	1
	1	1	0		1	0											0.5	0.5
	0	0	1		1	0
	1	0	1		0	1
	0	1	1		0	1
	1	1	1		1	0
					0.5	0.5
3)	Ahora tomamos el producto tensor para conseguir un repertorio sobre el estado futuro  formado por las dos partes en que se descompuso el sistema:
																										COMBINACION DEL SISTEMA PARTICIONADO
4)	Calculamos la distancia entre la distribucion de probabilidades del sistema sin descomponer (hecha en 1) y la distribución  del sistema descompuesto (realizada en 2) y 3))
	SISTEMA SIN DESCOMPONER
	COMBINACION DEL SISTEMA PARTICIONADO

## Sheet: EjemploVacio

	EJEMPLO DE UNA DESCOMPOSICIÓN DE UN SISTEMA

Aquí tenemos la distribución de probabilidades del sistema a analizar:
						B	0	1
			A	B	C
			0	0	0		1	0
			1	0	0		1	0
			0	1	0		1	0
			1	1	0		1	0
			0	0	1		1	0
			1	0	1		0	1
			0	1	1		1	0
 			1	1	1		0	1
Ahora calcularemos las distribuciones de probailidades de cada componente de la partición propuesta en este ejemplo:
					se marginaliza sobre el mecanismo
						E. Futuro
					E.Presente		B	0	1
					B	C							E. futuro
					0	0		1	0			E. actual		B	0	1
					0	0		1	0			B	C
					1	0		1	0			0	0		1	0
					1	0		1	0			1	0		1	0
					0	1		1	0			0	1		0.5	0.5
					0	1		0	1			1	1		0.5	0.5
					1	1		1	0
					1	1		0	1

Ahora calculamos el otro componente:

					Primero se hace la marginalización sobre C como se presenta a continuación:													Luego se hace la marginalización sobre B, como se presenta a 															Asi queda luego de las marginalizaciones:
							A	0	1	0	1	0	1	0	1			continuacion:			A	0	1	0	1	0	1	0	1						A	0	1	0	1	0	1	0	1
							B	0	0	1	1	0	0	1	1						B	0	0	1	1	0	0	1	1						B	0	0	1	1	0	0	1	1
					E. presente	E. futuro	C	0	0	0	0	1	1	1	1					E. futuro	C	0	0	0	0	1	1	1	1					E.futuro	C	0	0	0	0	1	1	1	1				A
					A	B													A														A
					0	0		1	0	0	0	0	0	0	0				0			0.5	0.5	0	0	0	0	0	0				0			0.25	0.25	0	0	0	0.5	0	0	1			1	1
					1	0		0	0	0	0	1	0	0	0				1			0	0	0	0	0.5	0	0	0.5				1			0	0.25	0	0.25	0.25	0	0	0.25	1
					0	1		0	0	0	0	0	1	0	0				0			0	0	0	0	0	1	0	0
					1	1		0	1	0	0	0	0	0	0				1			0	0.5	0	0.5	0	0	0	0
					0	0		0	1	0	0	0	0	0	0
					1	0		0	0	0	0	0	0	0	1
					0	1		0	0	0	0	0	1	0	0
					1	1		0	0	0	1	0	0	0	0

Ahora hacemos el producto tensor de las dos particiones
		E. Futuro
	E.Actual		B	0	1
	B	C					A
	0	0		1	0		1	1

						B	0	1
			A	B	C
			1	0	0		1	0

Ahora comparamos con la distribucion de probabilidades para 

						B	0	1
			A	B	C

			1	0	0	0	1	0

## Sheet: II

															estado futuro	A	0	1	0	1	0	1	0	1
																B	0	0	1	1	0	0	1	1
													Estado actual			C	0	0	0	0	1	1	1	1
													A	B	C
													0	0	0		1	0	0	0	0	0	0	0
													1	0	0		0	0	0	0	1	0	0	0
													0	1	0		0	0	0	0	0	1	0	0
													1	1	0		0	1	0	0	0	0	0	0
													0	0	1		0	1	0	0	0	0	0	0
													1	0	1		0	0	0	0	0	0	0	1
													0	1	1		0	0	0	0	0	1	0	0
													1	1	1		0	0	0	1	0	0	0	0
Vamos a calcular  la diatribución de probabilidades para el sistema completo
						Partimos de:
										B	0	1
							A	B	C
							0	0	0		1	0
							1	0	0		1	0				B	0	1
							0	1	0		1	0		A	B						B	0	1
							1	1	0		1	0		0	0		1	0		A
							0	0	1		1	0		1	0		0.5	0.5		0		1	0
							1	0	1		0	1		0	1		1	0		1		0.5	0.5
							0	1	1		1	0		1	1		0.5	0.5
							1	1	1		0	1

		Si queremos expandir el REPERTORIO EFECTO al espacio de estados completo para eso multiplicamos por la distribucion no restringida sobre los estados proximos de A y C
		así:
																			A	0	1	0	1	0	1	0	1
		A	0	1				B	0	1			C	0	1				B	0	0	1	1	0	0	1	1
			0.25	0.75			A							0.5	0.5				C	0	0	0	0	1	1	1	1
							1		0.5	0.5								A		0.0625	0.1875	0.0625	0.1875	0.0625	0.1875	0.0625	0.1875
Luego se calculara para la única partición posible para este subsistema cual es su distribución de probabilidades y luego se compara con la distribucion inicial del sistema sin partir
entonces  debemos calcular lo siguiente:
	P(ØF|AC)			P(BF|ØC)

1) Empezamos calculando P(ØF|AC), para esto marginalizamos en el estado t sobre B y C, asi:
		A	0	1	0	1	0	1	0	1					A	0	1	0	1	0	1	0	1
		B	0	0	1	1	0	0	1	1					B	0	0	1	1	0	0	1	1
	E. futuro	C	0	0	0	0	1	1	1	1				E. futuro	C	0	0	0	0	1	1	1	1
A													A														A
0			0.5	0.5	0	0	0	0	0	0			0			0.25	0.25	0	0	0	0.5	0	0
1			0	0	0	0	0.5	0	0	0.5			1			0	0.25	0	0.25	0.25	0	0	0.25				1	1
0			0	0	0	0	0	1	0	0
1			0	0.5	0	0.5	0	0	0	0
2)Ahora vamos a calcular  P(BF|ØC)
E.Actual		E. futuro	B	0	1
A	B	C
0	0	0		1	0
1	0	0		1	0
0	1	0		1	0
1	1	0		1	0
0	0	1		1	0
1	0	1		0	1
0	1	1		1	0
1	1	1		0	1
				0.75	0.25
																				B	0	1
									A				B	0	1				A
	P(ØF|AC)			P(BF|ØC)					1	1				0.75	0.25				1		0.75	0.25
Ahora calculamos la distancia entre el sistema sin partir y el sistema partido en la unica forma en que podía partirse:
							B	0	1
						A
						1
	SC: sistema  original 							0.5	0.5
												Aquí se comparan ambas distribuciones sin expandir sobre el espacio de estados completo
	SP: Sistema partido							0.75	0.25
							EMD (SO , SP) =  0,25*1

## Sheet: EMD

	Sea X1 y X2 dos variables aleatorias con su correspondiente espacio de estados (Por ej. X1=B y X2=C).  Si X1 y X2 son independientes  y
	sean p1 y q1 dos distribuciones de probabilidades en X1 y sean p2 y q2 dos distribuciones de probabilidades en X2																	Dado que los nodos son independientes, la EMD entre los repertorios efecto es igual a la suma de las EMD entre las distribuciones marginales de cada nodo,
																		 y la EMD entre las distribuciones marginales de un nodo es la diferencia absoluta en las probabilidades de que el nodo esté APAGADO.
			B	0	1	0	1
			C	0	0	1	1
		p		0.5	0	0.5	0								0.5	0.5
		Sea
		p1= (En B)
		p2= (En C)
			B	0	1	0	1
			C	0	0	1	1
		q		0.25	0.25	0.25	0.25
											0.5	0.5			0.5	0.5
		Sea
		q1= (En B)
		q2= (En C)
				EMD(p,q)  =  EMD(p1,q1)  + EMD(p2,q2)