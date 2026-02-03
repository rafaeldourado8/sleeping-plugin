# Análise de Complexidade Ciclomática

## Resumo Geral

**Total de blocos analisados:** 44  
**Complexidade média:** A (1.95)  

## Escala de Complexidade

- **A (1-5)**: Baixa complexidade - Simples, fácil de testar
- **B (6-10)**: Moderada - Razoável, pode precisar refatoração
- **C (11-20)**: Alta - Difícil de testar, requer refatoração
- **D (21-50)**: Muito alta - Crítico, refatorar urgentemente
- **F (>50)**: Extremamente alta - Não testável, reescrever

## Resultados por Arquivo

### ⚠️ camera_handler.py
```
CameraEventHandler._process_frame - B (6)  ← ATENÇÃO
CameraEventHandler - A (4)
handle_camera_removed - A (4)
handle_camera_added - A (3)
__init__ - A (1)
_trigger_alert - A (1)
```

**Análise:**
- `_process_frame` tem complexidade B (6) - único método que precisa atenção
- Motivo: Múltiplas condições (if session, if ear_value, if is_drowsy, if frame_counter)
- **Recomendação:** Extrair lógica de decisão para métodos separados

### ✅ detection_session.py
```
DetectionSession - A (2)
update_ear - A (1)
increment_frame_counter - A (1)
reset_frame_counter - A (1)
trigger_alert - A (1)
stop - A (1)
```

**Análise:** Excelente! Todos os métodos com complexidade A (1-2)

### ✅ domain_events.py
```
DomainEvent - A (2)
DrowsinessDetectedEvent - A (2)
AlertTriggeredEvent - A (2)
to_dict - A (1)
__init__ (todos) - A (1)
```

**Análise:** Perfeito! Eventos simples e diretos

### ✅ consumer.py
```
EventConsumer - A (3)
_on_message - A (3)
stop - A (3)
connect - A (2)
RabbitMQConfig - A (1)
__init__ - A (1)
register_handler - A (1)
start_consuming - A (1)
```

**Análise:** Boa! Complexidade controlada

### ✅ publisher.py
```
EventPublisher - A (2)
publish - A (2)
close - A (2)
PublisherConfig - A (1)
__init__ - A (1)
connect - A (1)
```

**Análise:** Excelente! Simples e direto

### ✅ drowsiness_detector.py
```
DrowsinessDetector - A (2)
calculate_ear - A (2)
detect - A (2)
__init__ - A (1)
euclidean_distance - A (1)
is_drowsy - A (1)
```

**Análise:** Perfeito! Lógica bem encapsulada

### ✅ stream_processor.py
```
_process_stream - A (5)
StreamProcessor - A (4)
stop - A (3)
start - A (2)
__init__ - A (1)
```

**Análise:** Bom! Complexidade aceitável para processamento de stream

## Métodos que Precisam Atenção

### 1. CameraEventHandler._process_frame (B - 6)

**Código atual:**
```python
def _process_frame(self, camera_id: str, frame):
    session = self.sessions.get(camera_id)
    if not session or not session.is_active:  # +1
        return
    
    ear_value = self.detector.detect(frame)
    if ear_value is None:  # +1
        return
    
    session.update_ear(ear_value)
    
    if self.detector.is_drowsy(ear_value):  # +1
        session.increment_frame_counter()
        
        if session.frame_counter >= self.consec_frames:  # +1
            self._trigger_alert(session)
    else:  # +1
        session.reset_frame_counter()
```

**Refatoração sugerida:**
```python
def _process_frame(self, camera_id: str, frame):
    session = self._get_active_session(camera_id)
    if not session:
        return
    
    ear_value = self._detect_ear(frame)
    if not ear_value:
        return
    
    self._update_session_state(session, ear_value)

def _get_active_session(self, camera_id: str):
    session = self.sessions.get(camera_id)
    return session if session and session.is_active else None

def _detect_ear(self, frame):
    return self.detector.detect(frame)

def _update_session_state(self, session, ear_value):
    session.update_ear(ear_value)
    
    if self.detector.is_drowsy(ear_value):
        self._handle_drowsy_state(session)
    else:
        session.reset_frame_counter()

def _handle_drowsy_state(self, session):
    session.increment_frame_counter()
    if session.frame_counter >= self.consec_frames:
        self._trigger_alert(session)
```

**Resultado:** Complexidade reduzida de B (6) para A (2) em cada método

## Métricas de Qualidade

### Distribuição de Complexidade
```
A (1-5):  43 métodos (97.7%)  ✅
B (6-10):  1 método  (2.3%)   ⚠️
C (11+):   0 métodos (0%)     ✅
```

### Complexidade por Camada
```
Domain:         A (1.5)  ✅ Excelente
Application:    A (3.2)  ✅ Bom (com 1 método B)
Infrastructure: A (2.1)  ✅ Excelente
```

## Conclusão

✅ **97.7% do código tem complexidade A** (baixa)  
⚠️ **Apenas 1 método com complexidade B** (moderada)  
✅ **Nenhum método com complexidade C ou superior**  

**Qualidade geral:** EXCELENTE

O código está muito bem estruturado seguindo SOLID. A única sugestão é refatorar `_process_frame` para reduzir de B para A.

## Comandos Úteis

```bash
# Complexidade ciclomática
radon cc src/ -a -s

# Complexidade com detalhes
radon cc src/ -a -s -n B

# Índice de manutenibilidade
radon mi src/ -s

# Métricas brutas (LOC, LLOC, etc)
radon raw src/ -s
```

## Referências

- McCabe, T. J. (1976). "A Complexity Measure"
- Limite recomendado: ≤ 10 (complexidade A ou B)
- Nosso código: 97.7% dentro do limite ✅
