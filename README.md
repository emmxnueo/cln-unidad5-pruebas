# Unidad 5 CLN · Integración, pruebas y calidad

Proyecto de la materia Componentes de Lógica de Negocios (FIME · UANL).
Parte del proyecto base de pedidos y lo extiende con reglas del sistema **FitZone**.

> El dominio de pedidos es un ejemplo didáctico. Las reglas de FitZone provienen del ADR-002 del equipo.

## Requisitos

- Python 3.11 o superior
- Git
- Cuenta de GitHub (para el pipeline de CI)

## Instalación

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Comandos

| Qué hace | Comando |
| --- | --- |
| Ejecutar todas las pruebas | `python -m pytest -v` |
| Solo pruebas de FitZone | `python -m pytest tests/test_fitzone.py -v` |
| Revisión de estilo | `python -m ruff check src tests` |
| Cobertura con umbral de 80 % | `python -m pytest -v --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=80` |
| Ver reporte HTML (macOS) | `open htmlcov/index.html` |

## Arquitectura

```
src/
  domain.py               Reglas de pedidos (descuento VIP, deuda, doble confirmación)
  application.py          OrderService: cobro mediante una pasarela inyectada
  repository.py           Persistencia SQLAlchemy de pedidos
  security.py             Política de cancelación (rol, propietario, 24 h)
  fitzone.py              Reglas de FitZone: lista de espera FIFO, oferta de 15 min,
                          asignación por retraso de 10 min, servicio de notificación
  fitzone_repository.py   Persistencia de la lista de espera
tests/
  test_order.py           Dominio de pedidos
  test_repository.py      Persistencia: commit y rollback
  test_service.py         Pasarela de pago simulada con Mock
  test_security.py        Autorización y límites de tiempo
  test_fitzone.py         Casos CP-01 a CP-13 de FitZone
casos_fitzone.csv         Matriz de casos de prueba
.github/workflows/ci.yml  Pipeline de calidad
```

Decisiones principales:

- **Dominio puro.** `domain.py` y `fitzone.py` no usan base de datos ni servicios externos, por lo que se prueban de forma rápida y aislada.
- **Dependencias inyectadas.** El servicio de cobro y el notificador reciben su dependencia como parámetro, así las pruebas usan `Mock` y no se hace ningún cargo ni envío real.
- **Fechas como parámetro.** Las reglas de tiempo reciben `now`, y las pruebas usan fechas fijas para que los resultados sean deterministas.
- **Persistencia aislada.** Las pruebas de repositorio usan SQLite en memoria; cada prueba crea su propio motor y no toca datos reales. SQLite en memoria no sustituye las pruebas en un motor productivo como PostgreSQL.

## Reglas de FitZone cubiertas

1. **Lista de espera FIFO:** el primer socio en la fila recibe el lugar liberado por una cancelación.
2. **Ventana de confirmación de 15 minutos:** pasado ese tiempo la oferta vence.
3. **Retraso de 10 minutos:** el lugar se asigna de inmediato a un socio presente.

Los límites de tiempo son inclusivos (15 y 10 minutos exactos cuentan). Esta decisión debe confirmarse contra el ADR-002.

## Pipeline de CI

En cada `push` y `pull request`, GitHub Actions ejecuta Ruff, pytest con cobertura mínima del 80 % y `compileall`. El pipeline verifica la construcción, no hace despliegue. Para impedir fusionar cambios con el CI en rojo hay que activar branch protection o rulesets en la configuración del repositorio.

## Limitaciones conocidas

- `OrderService.checkout()` confirma el pedido antes de cobrar; si el pago es rechazado, el pedido queda en `CONFIRMED`. Se propone un estado intermedio `PENDING_PAYMENT`.
- En FitZone, el rechazo de un socio duplicado en la lista de espera no tiene prueba, y no está implementado qué ocurre con el siguiente socio cuando una oferta vence.
- El proyecto no incluye API web, interfaz ni pruebas E2E reales.