# Exportación de Planillas — Oracle + Streamlit

App web interna para exportar planillas desde Oracle a CSV, con un flujo simple:

```
Buscar código → Preparar descarga → Descargar CSV
```

---

## 🚀 Arrancar / Detener

### Con systemd (recomendado — auto-arranque al encender)

```bash
sudo systemctl status  streamlit-planillas   # Ver si está corriendo
sudo systemctl start    streamlit-planillas   # Iniciar
sudo systemctl stop     streamlit-planillas   # Detener
sudo systemctl restart  streamlit-planillas   # Reiniciar
```

### Manual (para pruebas)

```bash
cd ~/codex_projects/cobertura_lopez/streamlit_oracle_app
source .venv/bin/activate
export JAVA_TOOL_OPTIONS="-Doracle.jdbc.timezoneAsRegion=false -Duser.timezone=UTC"
export STREAMLIT_SERVER_PORT=8889
streamlit run app.py --server.headless false
```

---

## 🌐 Acceso

| Red | URL |
|-----|-----|
| Local (servidor) | http://localhost:8501 |
| Red interna | http://192.168.60.74:8501 |

---

## 🧭 Flujo de uso

1. Abrir la URL en el navegador
2. Ingresar credenciales Oracle (usuario/contraseña de BD)
3. Escribir el **código de generación** y presionar **Buscar**
4. Si hay registros, se habilita **Preparar descarga**
5. Presionar **Preparar descarga** (la pantalla no se congela)
6. Cuando termine, aparece **Descargar CSV** (verde)
7. El CSV se descarga **sin encabezado**, en UTF-8
8. Para salir, presionar **Salir** abajo

---

## 📁 Estructura del proyecto

```
streamlit_oracle_app/
├── app.py                     ← Punto de entrada
├── .env.example               ← Ejemplo de configuración
├── .env                       ← Config real (protegido chmod 600)
├── requirements.txt           ← Dependencias Python
├── jdbc/
│   └── ojdbc8.jar             ← Driver Oracle JDBC
├── src/
│   ├── config.py              ← Variables de entorno
│   ├── oracle_jdbc.py         ← Conexión Oracle con failover + timeout
│   ├── export_planillas.py    ← Buscar código + exportar CSV por lotes
│   ├── async_jobs.py          ← Ejecución en 2º plano (no freeze)
│   ├── auth.py                ← Login contra Oracle
│   ├── ui.py                  ← Estilos CSS globales
│   └── pages/
│       └── dashboard.py       ← Pantalla principal (minimalista)
├── backups_codigo/            ← Respaldos viejos (seguros ignorar)
└── .venv/                     ← Entorno virtual Python
```

---

## ⚙️ Configuración (`.env`)

```env
ORACLE_JDBC_JAR=jdbc/ojdbc8.jar
ORACLE_TARGETS=host1:1521:sid1,host2:1521:sid2
MAX_WORKERS=4
DEFAULT_MAX_ROWS=500
```

- `ORACLE_TARGETS` — nodos RAC, separados por coma
- `MAX_WORKERS` — hilos para consultas concurrentes

---

## 🧹 Limpieza automática

Los CSV se guardan en `/tmp/streamlit_oracle_exports/` y se eliminan automáticamente cada madrugada (2:00 AM) vía cron.

```bash
crontab -l   # Ver tarea programada
```

---

## 📊 Límites del servicio

| Recurso | Límite |
|---------|--------|
| RAM máxima | 250 MB |
| RAM recomendada (soft) | 220 MB |
| Tareas/hilos máximos | 100 |
| Tiempo de búsqueda | 60 segundos |
| Tiempo de exportación | 600 segundos |

Si el proceso supera 250 MB de RAM, systemd lo mata y lo reinicia automáticamente.

---

## 🔐 Seguridad

- La contraseña Oracle **no se guarda en disco**, solo en memoria de sesión
- El SQL **no se muestra al usuario**
- Solo se permiten consultas `SELECT`
- El `.env` está protegido (`chmod 600`)
- El firewall solo acepta conexiones de la red `172.16.0.0/16`
- El usuario Oracle debería tener solo permisos de `SELECT` sobre `DIGITALIZACION`

---

## 🔧 Mantenimiento

### Ver logs del servicio

```bash
journalctl -u streamlit-planillas -f
```

### Ver consumo de RAM

```bash
sudo systemctl status streamlit-planillas --no-pager | grep Memory
```

### Actualizar código

```bash
cd ~/codex_projects/cobertura_lopez
git pull
sudo systemctl restart streamlit-planillas
```

### Backup rápido

```bash
cd ~/codex_projects/cobertura_lopez
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz streamlit_oracle_app/
```

---

## 🛠️ Resolver problemas comunes

| Problema | Causa probable | Solución |
|----------|---------------|----------|
| No carga la página | Servicio caído | `sudo systemctl restart streamlit-planillas` |
| Error "Port not available" | Puerto ocupado | `sudo kill -9 $(lsof -ti:8501)` y reiniciar |
| Login falla | Credenciales o RAC caído | Revisar `.env` > `ORACLE_TARGETS` |
| Exportación lenta | Muchos registros | Aumentar `timeout_seconds` en `dashboard.py` |
| Proceso muerto por RAM | Superó 250 MB | Revisar `journalctl -u streamlit-planillas -e` |

---

## 📝 Notas técnicas

- Python 3.12 + Streamlit 1.57
- Conexión Oracle vía JDBC (JayDeBeApi + JPype1)
- Java OpenJDK 21
- El CSV se escribe fila por fila con `csv.writer`, no carga todo en memoria
- No usa `pandas` para exportación (solo para posible consulta futura)
