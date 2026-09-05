"""Datos curriculares locales de respaldo para la demo de Currícula Viva.

El backend/API sigue siendo la fuente preferida cuando está disponible.
Estos datos permiten que la demo de Streamlit funcione por sí sola.
"""

UNIVERSITY = {"id": 1, "name": "Universidad Nacional de Ingeniería", "code": "UNI", "country": "Perú"}

PROGRAMS = [
    {"id": 1, "name": "Ingeniería Eléctrica", "plan_period": "2018-2"},
    {"id": 2, "name": "Ingeniería Electrónica", "plan_period": "2018-2"},
    {"id": 3, "name": "Ingeniería de Telecomunicaciones", "plan_period": "2025-1"},
]


def _courses(rows):
    return [
        {"id": i + 1, "course_code": code, "course_name": name, "cycle": cycle,
         "hours": hours, "mandatory": mandatory}
        for i, (code, name, cycle, hours, mandatory) in enumerate(rows)
    ]

# Cursos tomados de los planes de estudio suministrados para la demo.
COURSES = {
1: _courses([
("BAE01","Actividades Extracurriculares",1,1,True),("BFI01","Física I",1,8,True),
("BIC01","Introducción a la Computación",1,5,True),("BMA01","Cálculo Diferencial",1,6,True),
("BMA03","Álgebra Lineal",1,5,True),("BRN01","Realidad Nacional, Constitución y Derechos Humanos",1,4,True),
("EE250","Dibujo Técnico",1,6,True),("BFI05","Fundamentos de Ingeniería Térmica y de Fluidos",2,5,True),
("BMA02","Cálculo Integral",2,6,True),("BMA09","Algoritmos y Estructuras de Datos I",2,4,True),
("BQU01","Química I",2,8,True),("BRC01","Redacción y Comunicación",2,3,True),
("EE152","Fundamentos de Ingeniería del Computador",2,5,True),
("BEG01","Economía General",3,4,True),("BFI03","Fundamentos de Electricidad, Magnetismo y Óptica",3,6,True),
("BMA05","Ecuaciones Diferenciales",3,6,True),("BMA10","Probabilidades y Estadística",3,4,True),
("BMA15","Programación Orientada a Objetos",3,4,True),("EE306","Electrotecnia e Instalación de Redes",3,4,True),
("BEF01","Ética y Filosofía Política",4,3,True),("BFI06","Introducción a la Física Moderna",4,5,True),
("BIE01","Idioma Extranjero",4,2,True),("BMA07","Cálculo Vectorial",4,5,True),
("BMA18","Métodos Numéricos",4,4,True),("EE320","Circuitos Eléctricos I",4,7,True),
("EE410","Análisis de Señales y Sistemas",4,5,True),
("BFM16","Mecánica de Fluidos y Termodinámica",5,5,True),("EE418","Dispositivos y Circuitos Electrónicos I",5,5,True),
("EE420","Circuitos Eléctricos II",5,7,True),("EE428","Laboratorio de Electrónica I",5,2,True),
("EE522","Electromagnetismo I",5,5,True),("EE647","Sistemas de Control I",5,5,True),
("BFM17","Fundamentos de Turbomáquinas",6,4,True),("EE238","Medidas Eléctricas I",6,4,True),
("EE288","Máquinas Eléctricas I",6,5,True),("EE353","Análisis de Sistemas de Potencia I",6,6,True),
("EE239","Medidas Eléctricas II",7,4,True),("EE241","Laboratorio de Máquinas Eléctricas I",7,3,True),
("EE298","Máquinas Eléctricas II",7,5,True),("EE354","Análisis de Sistemas de Potencia II",7,5,True),
("EE532","Electrónica de Potencia",7,7,True),("BEG06","Formulación y Evaluación de Proyectos",8,4,True),
("EE242","Laboratorio de Máquinas Eléctricas II",8,3,True),("EE393","Líneas de Transmisión de Potencia",8,4,True),
("EE470","Instalaciones Eléctricas Industriales",8,5,True),("EE445","Proyecto de Fin de Carrera",9,6,True),
("EE676","Centrales Eléctricas I",9,4,True),("EE698","Laboratorio de Sistemas Eléctricos de Potencia",9,2,True),
("EE446","Proyecto de Tesis",10,6,True),("EE349","Gestión de la Energía",8,4,False),
("EE350","Legislación Eléctrica",8,4,False),("EE355","Optimización de Sistemas de Potencia",8,5,False),
("EE356","Operación y Control de Sistemas de Potencia",8,5,False),("EE357","Calidad de Energía",8,4,False),
("EE360","Generación Distribuida y Redes Inteligentes",9,5,False),("EE376","Protección de Sistemas de Potencia",9,5,False),
("EE679","Subestaciones Eléctricas",9,4,False),("EE704","Generación Eléctrica con Energías Renovables",10,4,False),
("EE705","Generación Eléctrica con Energía Solar Aplicada",10,4,False),
]),
2: _courses([
("BAE01","Actividades Extracurriculares",1,1,True),("BFI01","Física I",1,8,True),
("BIC01","Introducción a la Computación",1,5,True),("BMA01","Cálculo Diferencial",1,6,True),
("BMA03","Álgebra Lineal",1,5,True),("BRN01","Realidad Nacional, Constitución y Derechos Humanos",1,4,True),
("EE250","Dibujo Técnico",1,6,True),("BFI05","Fundamentos de Ingeniería Térmica y de Fluidos",2,5,True),
("BMA02","Cálculo Integral",2,6,True),("BMA09","Algoritmos y Estructuras de Datos I",2,4,True),
("BQU01","Química I",2,8,True),("BRC01","Redacción y Comunicación",2,3,True),
("EE152","Fundamentos de Ingeniería del Computador",2,5,True),("BEG01","Economía General",3,4,True),
("BFI03","Fundamentos de Electricidad, Magnetismo y Óptica",3,6,True),("BMA05","Ecuaciones Diferenciales",3,6,True),
("BMA10","Probabilidades y Estadística",3,4,True),("BMA15","Programación Orientada a Objetos",3,4,True),
("EE306","Electrotecnia e Instalación de Redes",3,4,True),("BEF01","Ética y Filosofía Política",4,3,True),
("BFI06","Introducción a la Física Moderna",4,5,True),("BIE01","Idioma Extranjero",4,2,True),
("BMA07","Cálculo Vectorial",4,5,True),("BMA18","Métodos Numéricos",4,4,True),
("EE320","Circuitos Eléctricos I",4,7,True),("EE410","Análisis de Señales y Sistemas",4,5,True),
("EE418","Dispositivos y Circuitos Electrónicos I",5,5,True),("EE420","Circuitos Eléctricos II",5,7,True),
("EE428","Laboratorio de Electrónica I",5,2,True),("EE430","Sistemas de Comunicaciones I",5,6,True),
("EE522","Electromagnetismo I",5,5,True),("EE647","Sistemas de Control I",5,5,True),
("EE438","Dispositivos y Circuitos Electrónicos II",6,5,True),("EE458","Laboratorio de Electrónica II",6,2,True),
("EE588","Electromagnetismo II",6,5,True),("EE604","Introducción a Microcontroladores",6,4,True),
("EE648","Sistemas de Control II",6,6,True),("EE528","Conversión de Energía Electromecánica",7,6,True),
("EE530","Sistemas de Comunicaciones II",7,6,True),("EE644","Diseño Lógico Digital",7,6,True),
("EE678","Instrumentación y Control de Procesos Industriales",7,6,True),
("BEG06","Formulación y Evaluación de Proyectos",8,4,True),("EE468","Electrónica de Radiocomunicaciones",8,5,True),
("EE532","Electrónica de Potencia",8,7,True),("EE445","Proyecto de Fin de Carrera",9,6,True),
("EE498","Laboratorio de Radiocomunicaciones",9,2,True),("EE446","Proyecto de Tesis",10,6,True),
("EE592","Microondas",9,6,False),("EE594","Antenas",9,4,False),("EE590","Comunicaciones por Fibra Óptica",9,6,False),
("EE548","Redes Inalámbricas y Móviles",9,4,False),("EE608","Sistemas de Comunicaciones Satelitales",10,4,False),
("EE681","Arquitectura de Computadores de Procesamiento Paralelo",10,6,False),
("EE689","Arquitectura de Microcontroladores Avanzados",10,4,False),
]),
3: _courses([
("BAE01","Actividades Extracurriculares",1,1,True),("BFI01","Física I",1,8,True),
("BIC01","Introducción a la Computación",1,5,True),("BMA01","Cálculo Diferencial",1,6,True),
("BMA03","Álgebra Lineal",1,5,True),("BRN01","Realidad Nacional, Constitución y Derechos Humanos",1,4,True),
("CBS01","Fundamentos de Programación",1,4,True),("BFI05","Fundamentos de Ingeniería Térmica y de Fluidos",2,5,True),
("BMA02","Cálculo Integral",2,6,True),("BMA09","Algoritmos y Estructuras de Datos I",2,4,True),
("BQU01","Química I",2,8,True),("BRC01","Redacción y Comunicación",2,3,True),
("CBS02","Sistemas Operativos I",2,4,True),("BEG01","Economía General",3,4,True),
("BFI03","Fundamentos de Electricidad, Magnetismo y Óptica",3,6,True),("BMA05","Ecuaciones Diferenciales",3,6,True),
("BMA10","Probabilidades y Estadística",3,4,True),("BMA15","Programación Orientada a Objetos",3,4,True),
("EE306","Electrotecnia e Instalación de Redes",3,4,True),("BEF01","Ética y Filosofía Política",4,3,True),
("CBN01","Redes de Datos I",4,5,True),("BMA07","Cálculo Vectorial",4,5,True),("BMA18","Métodos Numéricos",4,4,True),
("EE320","Circuitos Eléctricos I",4,7,True),("EE410","Análisis de Señales y Sistemas",4,5,True),
("BMA22","Procesos Estocásticos y Teoría de la Información",5,7,True),("TLR01","Dispositivos de Radiofrecuencia",5,5,True),
("TLN01","Enrutamiento y Conmutación de Redes de Datos",5,7,True),("EE428","Laboratorio de Electrónica I",5,2,True),
("EE522","Electromagnetismo I",5,5,True),("CBS05","Inteligencia Artificial I",5,5,True),
("EE430","Sistemas de Comunicaciones I",6,6,True),("TLR02","Circuitos de Radiofrecuencia",6,5,True),
("EE458","Laboratorio de Electrónica II",6,2,True),("EE588","Electromagnetismo II",6,5,True),
("EE604","Introducción a los Microcontroladores",6,4,True),("TLN02","Seguridad de Redes Empresariales",6,6,True),
("TLR03","Sistemas de Antenas",7,5,True),("EE530","Sistemas de Comunicaciones II",7,6,True),
("EE590","Comunicaciones por Fibra Óptica",7,6,True),("BEG06","Formulación y Evaluación de Proyectos",8,4,True),
("EE498","Laboratorio de Radiocomunicaciones",8,2,True),("EE592","Microondas",8,6,True),
("TLR04","Redes Inalámbricas y Móviles I",9,4,True),("CIB45","Taller de Proyecto de Investigación",9,6,True),
("TLR05","Normas Legales y Técnicas de las Telecomunicaciones",9,4,True),
("EE712","Planificación de Redes de Telecomunicaciones",10,4,True),("CIB46","Taller de Investigación",10,6,True),
("TLN03","Automatización y Programabilidad de Redes",8,4,False),("TLN04","Enrutamiento Avanzado",8,4,False),
("TLN05","Arquitectura de Servidores y Centro de Datos",8,4,False),("TLN06","Gestión y Monitoreo de Redes Empresariales",8,6,False),
("TLN07","Fundamentos de Computación en la Nube",9,4,False),("TLN08","Arquitectura de Redes Virtuales",9,6,False),
("TLN09","Automatización en la Nube",10,4,False),("CBN03","Seguridad en Redes Industriales I",10,5,False),
("CBN07","Seguridad de Redes Móviles",10,4,False),("CBS37","Internet de las Cosas",10,4,False),
("TLR08","Redes de Comunicaciones Ópticas",10,4,False),("CBS33","Radio Definida por Software",10,4,False),
]),
}

GAPS = {
1: [
 {"id":101,"competency":"Analizar y operar sistemas de potencia eléctrica","severity":0.78,"coverage":0.42,"essential":True,"hours_associated":11,"occupations":["Ingeniero de sistemas de potencia"],"action":"Revisar la articulación entre análisis de potencia, operación y protección."},
 {"id":102,"competency":"Diseñar y evaluar instalaciones eléctricas","severity":0.69,"coverage":0.51,"essential":True,"hours_associated":9,"occupations":["Ingeniero de instalaciones eléctricas"],"action":"Fortalecer evidencia aplicada de diseño y evaluación de instalaciones."},
 {"id":103,"competency":"Gestionar calidad y confiabilidad de energía","severity":0.61,"coverage":0.57,"essential":False,"hours_associated":4,"occupations":["Ingeniero de calidad de energía"],"action":"Consolidar contenidos de calidad, confiabilidad y mantenimiento."},
 {"id":104,"competency":"Integrar generación distribuida y redes inteligentes","severity":0.56,"coverage":0.63,"essential":True,"hours_associated":5,"occupations":["Ingeniero de redes eléctricas inteligentes"],"action":"Articular generación distribuida, control y redes inteligentes."},
],
2: [
 {"id":201,"competency":"Diseñar sistemas electrónicos analógicos y digitales","severity":0.72,"coverage":0.48,"essential":True,"hours_associated":16,"occupations":["Ingeniero electrónico"],"action":"Reforzar trazabilidad entre dispositivos, circuitos y diseño."},
 {"id":202,"competency":"Desarrollar sistemas embebidos y microcontroladores","severity":0.65,"coverage":0.55,"essential":True,"hours_associated":4,"occupations":["Ingeniero de sistemas embebidos"],"action":"Integrar microcontroladores con prácticas y proyectos aplicados."},
 {"id":203,"competency":"Implementar sistemas de comunicaciones","severity":0.59,"coverage":0.61,"essential":True,"hours_associated":12,"occupations":["Ingeniero de comunicaciones"],"action":"Conectar comunicaciones, RF y laboratorio mediante proyectos."},
 {"id":204,"competency":"Automatizar e instrumentar procesos industriales","severity":0.52,"coverage":0.66,"essential":False,"hours_associated":6,"occupations":["Ingeniero de automatización"],"action":"Aumentar evidencia práctica de instrumentación y control."},
],
3: [
 {"id":301,"competency":"Configurar y administrar redes de datos","severity":0.74,"coverage":0.49,"essential":True,"hours_associated":12,"occupations":["Ingeniero de redes"],"action":"Consolidar enrutamiento, conmutación y monitoreo de redes."},
 {"id":302,"competency":"Diseñar sistemas de radiofrecuencia y antenas","severity":0.68,"coverage":0.54,"essential":True,"hours_associated":14,"occupations":["Ingeniero de radiofrecuencia"],"action":"Integrar RF, antenas, microondas y laboratorio."},
 {"id":303,"competency":"Implementar comunicaciones ópticas","severity":0.58,"coverage":0.62,"essential":True,"hours_associated":6,"occupations":["Ingeniero de comunicaciones ópticas"],"action":"Reforzar continuidad entre fibra óptica y redes de comunicaciones."},
 {"id":304,"competency":"Planificar y optimizar redes de telecomunicaciones","severity":0.55,"coverage":0.64,"essential":True,"hours_associated":4,"occupations":["Ingeniero de planificación de redes"],"action":"Vincular planificación de redes con indicadores de desempeño."},
]
}


def evidence(gap_id):
    mapping = {
        101:["EE353","EE354"],102:["EE470","EE346"],103:["EE357","EE351"],104:["EE360"],
        201:["EE418","EE438"],202:["EE604","EE689"],203:["EE430","EE530"],204:["EE678","EE647"],
        301:["CBN01","TLN01"],302:["TLR01","TLR03","EE592"],303:["EE590","TLR08"],304:["EE712"],
    }
    for pid, gaps in GAPS.items():
        for gap in gaps:
            if gap["id"] == gap_id:
                selected = [c for c in COURSES[pid] if c["course_code"] in mapping[gap_id]]
                return {
                    "competency": gap["competency"], "occupations": gap["occupations"], "action": gap["action"],
                    "courses": [
                        {**c, "unit_name": "Contenido curricular", "similarity": max(0.61, gap["coverage"] + 0.10)}
                        for c in selected
                    ],
                }
    return {}
