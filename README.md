# 🥗 NutriMatch - Sistema de Recomendación Nutricional Inteligente

## 📋 Descripción del Proyecto

**NutriMatch** es un sistema de recomendación nutricional inteligente desarrollado con Django que utiliza algoritmos de machine learning para proporcionar sugerencias personalizadas de alimentos basadas en los objetivos, preferencias y patrones de consumo de cada usuario.

---

## ✨ Características Principales

### 🧠 Sistema de Recomendación Inteligente
- Algoritmo híbrido que combina filtrado colaborativo y basado en contenido  
- Recomendaciones contextuales por tipo de comida (desayuno, almuerzo, cena, snack)  
- Aprendizaje automático basado en patrones de consumo y calificaciones del usuario  
- Score multifactorial considerando nutrición, preferencias, variedad y conveniencia  

### 📊 Seguimiento Nutricional Completo
- Dashboard interactivo con visualización en tiempo real de macronutrientes  
- Cálculo automático de necesidades nutricionales basado en objetivos personales  
- Análisis de adherencia diaria y tendencias históricas  
- Alertas inteligentes para mantener balance nutricional  

### 🔍 Base de Datos Nutricional Extensa
- Más de 8,000 alimentos con información nutricional detallada  
- Datos basados en USDA FoodData Central  
- Integración con API externa para expandir catálogo en tiempo real  
- Búsqueda avanzada con filtros por macronutrientes, restricciones dietéticas y categorías  

### 👤 Personalización Avanzada
- Perfiles personalizados basados en edad, peso, altura, género y nivel de actividad  
- Soporte para objetivos específicos (perder peso, ganar músculo, mantener salud)  
- Gestión de restricciones dietéticas (vegetariano, vegano, sin gluten, keto, etc.)  
- Sistema de alergias y preferencias alimentarias  

### 📈 Análisis y Progreso
- Gráficos interactivos de tendencias nutricionales  
- Análisis de patrones de consumo y alimentos más frecuentes  
- Insights automatizados y recomendaciones de mejora  
- Historial completo de consumo con métricas de adherencia  

---

## 🛠️ Stack Tecnológico

### Backend
- **Framework:** Django 4.2 + Django REST Framework  
- **Base de Datos:** MySQL  
- **Machine Learning:** Scikit-learn, NumPy, Pandas  
- **APIs Externas:** USDA FoodData Central API  

### Frontend
- **Plantillas:** HTML5, CSS3, Bootstrap 5  
- **JavaScript:** Vanilla JS + Chart.js para visualizaciones  
- **UI/UX:** Diseño responsive y moderno  

### Arquitectura
- **Patrón:** MVT (Model-View-Template) de Django  
- **APIs:** RESTful para integración con aplicaciones externas  
- **Autenticación:** Sistema de usuarios personalizado con perfiles extendidos  

---

## 🚀 Funcionalidades Implementadas

### Sistema de Usuarios
- ✅ Registro y autenticación completa
  📸 **![Panel Principal](capturas/menu.png)**
- ✅ Configuración de perfil nutricional personalizado
- ✅ Gestión de preferencias y restricciones dietéticas
  📸 **![Datos del Usuario Resgistrado](capturas/datos.png)**

### Motor de Recomendaciones
- ✅ Algoritmo híbrido de recomendación  
- ✅ Recomendaciones contextuales por horario de comida  
- ✅ Sistema de scoring multifactorial  
- ✅ Aprendizaje automático basado en feedback del usuario
  📸 **![Recomendacion basado al Usuario](capturas/recomendacioncomidas.png)**

### Gestión de Alimentos
- ✅ Base de datos de 8,000+ alimentos  
- ✅ Búsqueda avanzada con autocompletado  
- ✅ Importación de datos desde CSV  
- ✅ Integración con USDA API  

### Seguimiento y Análisis
- ✅ Registro de consumo diario  
- ✅ Dashboard con métricas en tiempo real  
- ✅ Gráficos de progreso histórico  
- ✅ Sistema de calificación de alimentos
  📸 **![Recomendacion basado al Usuario](capturas/progreso.png)**

---



## 🔬 Algoritmos y Machine Learning

### Motor de Recomendación
- **Filtrado Colaborativo:** Basado en similitud entre usuarios  
- **Filtrado por Contenido:** Análisis de propiedades nutricionales  
- **Optimización Nutricional:** Balanceo automático de macronutrientes  
- **Diversidad:** Algoritmos para evitar monotonía alimentaria  

### Análisis Predictivo
- Predicción de adherencia a objetivos  
- Identificación de patrones de consumo  
- Recomendaciones proactivas de ajustes nutricionales  
- Análisis de tendencias de salud  

---

## 🧪 Instalación y Ejecución

### 1. Clona el repositorio
```bash
git clone https://github.com/alex-raul/nutrimatch-sistema-de-recomendacion-inteligente2.git
cd nutrimatch-sistema-de-recomendacion-inteligente2

### 2. Crear entorno virtual
# Windows
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

##  Configura las variables de entorno
Crea un archivo .env en la raíz del proyecto y agrega lo siguiente:
# .env
SECRET_KEY='django-insecure-06a97tg1dx-$6mucbrzm=u#fy@j_-covk&pj^6fsxy*yf_oes3'
DEBUG=True

# Base de datos MySQL
DB_NAME=nutrimatch_db
DB_USER=root
DB_PASSWORD=......
DB_HOST=localhost
DB_PORT=3306

# API Keys
# USDA_API_KEY=your-api-key-here


## 5. Aplica migraciones de la base de datos
python manage.py makemigrations
python manage.py migrate

## 6. Ejecuta el servidor de desarrollo
python manage.py runserver
