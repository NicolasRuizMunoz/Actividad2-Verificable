## Cómo ejecutar el aplicativo ##
Para ejecutar el aplicativo se deben seguir los siguientes pasos:
* Ejecutar el docker compose que se encuentra en la carpeta ```db``` con el comando ```docker compose up```
    * Debe tener instalado ```docker``` en su máquina para poder ejecutar ese comando
* Se debe ingresar a la base de datos con algún administrador de base de datos relacional de preferencia (Databind, DBeaver, etc) y crear la tabla de registros que se encuentra en la carpeta ```db``` en el archivo ```db.sql```
* Instalar las bibliotecas que se encuentran en el archivo ```requirements.txt``` utilizando el comando ```pip install -r requirements.txt```
    * NOTA: Si el comando anterior no funciona puedes utilizarlo indicando que se ejecute desde python con ```python -m pip install -r requirements.txt```
* Crear un archivo ```.env``` que contenga lo siguiente:
    ```
    MYSQL_HOST='localhost'
    MYSQL_PORT=3306
    MYSQL_DATABASE='test_poc'
    MYSQL_USER='user'
    MYSQL_PASSWORD='pass'
    ```

## IMPORTANTE: ##

Para cargar los datos en la aplicación, se utiliza un sistema de archivos JSON y el sistema espera los siguientes archivos:

1. Archivos necesarios para la carga de datos:
   * `1-alumnos.json`: Contiene la información de los estudiantes
   * `2-profesores.json`: Contiene la información de los profesores
   * `3-cursos.json`: Contiene la información base de los cursos
   * `4-instancias_cursos.json`: Contiene las instancias de los cursos
   * `5-instancia_cursos_con_secciones.json`: Contiene las secciones de cada instancia
   * `6-alumnos_por_seccion.json`: Contiene la asignación de alumnos a secciones
   * `7-notas_alumnos.json`: Contiene las notas de los alumnos
   * `8-salas_de_clases.json`: Contiene la información de las salas disponibles

2. Carga de datos:
   * Los archivos JSON pueden ser subidos individualmente a través de la interfaz web
   * También se puede realizar una carga masiva de todos los archivos a la vez
   * En el último caso, los archivos deben estar ubicados en la carpeta `data/`

3. Generación de horarios:
   * Una vez cargados los datos, utilizar el botón "Crear Horario"
   * Después de la creación, aparecerá la opción "Descargar Horario" para obtener el horario generado

* Ejecutar la aplicación desde ```main.py``` con el comando ```python ./main.py```
    * Por defecto la aplicación se ejecuta en ```localhost``` en el puerto ```5000```

### Explicación de nuestro algoritmo ###

El algoritmo que utilizamos para generar los horarios sigue un enfoque heurístico que prioriza las secciones más difíciles de programar. El proceso es el siguiente:

1. Restricciones del horario:
   * Horario disponible: 9:00 - 18:00
   * Hora de almuerzo: 13:00 - 14:00 (bloqueada)
   * Días disponibles: Lunes a Viernes

2. Para cada sección, calculamos:
   * Puntaje de flexibilidad: cantidad de slots posibles donde se puede programar
   * Puntaje de conflictos: basado en superposiciones potenciales con otros cursos
   * Cantidad de estudiantes y créditos del curso

3. Ordenamos las secciones para programar primero:
   * Las que tienen menor flexibilidad (menos opciones disponibles)
   * Las que tienen mayor puntaje de conflictos
   * Las que tienen más créditos
   * Las que tienen más estudiantes

4. Para cada sección, el algoritmo:
   * Busca salas adecuadas según la cantidad de estudiantes
   * Encuentra slots de tiempo donde no hay conflictos con:
     - Horarios de profesores
     - Horarios de estudiantes
     - Disponibilidad de salas
   * Asigna el primer slot válido encontrado

Este enfoque nos permite generar horarios que:
* Respetan las restricciones de capacidad de salas
* Evitan conflictos de horarios para profesores y estudiantes
* Priorizan las secciones más complejas de programar
* Optimizan el uso de los recursos disponibles


### Features ###

1. Cierre de Cursos:
   * Cuando un curso se marca como "cerrado":
     - Se deshabilita la opción de editar información del curso
     - No se pueden agregar nuevas instancias al curso
     - No se pueden modificar las secciones existentes
     - No se pueden agregar o quitar estudiantes de las secciones
     - Se mantiene visible la información del curso pero en modo de solo lectura
   * Esta funcionalidad ayuda a:
     - Prevenir modificaciones accidentales una vez que el curso está en marcha
     - Mantener la integridad de los datos históricos
     - Facilitar la gestión de cursos activos vs. finalizados
     

## Cómo ejecutar las pruebas ##
En esta prueba de concepto existe un archivo de pruebas unitarias (```test.py```) que permite evaluar la funcionalidad de cada uno de los aplicativos, se puede ejecutar el test utilizando el siguiente comando:

```pytest test.py```

Si no funciona el comando anterior, se puede ejecutar desde python con el siguiente comando:

```python -m pytest test.py```

Con las bibliotecas ```coverage``` y ```pytest-cov``` se pueden generar reportes de cobertura de código después de ejecutar los tests, para ello se debe ejecutar el siguiente comando:

```pytest --cov=. test.py --cov-report html```

Si no funciona el comando anterior, se puede ejecutar desde python con el siguiente comando:

```python -m pytest --cov=. test.py --cov-report html```

Ya con el reporte generado, se debe haber creado una carpeta llamada ```htmlcov```, dentro de ésta se muestrá un archivo ```index.html```, al abrirlo se mostrará la cobertura de codigo a través de los tests.


## Extensiones para verificar código limpio
En esta sección se propondran extensiones/plugins que pueden instalar para verificar que cumplen con parte de las buenas prácticas del codigo limpio (clean code)

* SonarLint: Extensión para encontrar y corregir problemas de codificación en tiempo real, marcando los problemas a medida que codifica, similar a un corrector ortográfico. Se puede instalar como un plugin en Intellij o como extensión en Visual Studio Code.
* Code Spell Checker: Extensión que ayuda a detectar nombres de variables que puedan tener algun problema de nombre ya sea por falta ortográfica o por incoherencia. Se puede instalar en Visual Studio Code en muchos idiomas incluyendo Español. En Intellij viene por defecto.
