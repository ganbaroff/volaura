# VOLAURA VM Deploy — самый лёгкий путь

## Вариант 1: GCP (у нас $1,300 кредитов)

### Создать VM (5 минут в консоли)

1. Зайди console.cloud.google.com → Compute Engine → Create Instance
2. Настройки:
   - Name: `volaura-swarm`
   - Region: `us-central1` (дешевле)
   - Machine: `n1-standard-4` (4 vCPU, 15GB RAM) — $0.19/час = ~$140/мес
   - GPU: `NVIDIA T4` — $0.35/час = ~$250/мес (итого ~$390/мес, хватит на 3 мес)
   - Boot disk: Ubuntu 22.04, 50GB SSD
   - Firewall: Allow SSH

3. SSH и запуск:
```bash
# Подключись
gcloud compute ssh volaura-swarm

# Установи NVIDIA drivers + CUDA
sudo apt install -y nvidia-driver-535 nvidia-cuda-toolkit

# Установи Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Клонируй проект
git clone https://github.com/ganbaroff/VOLAURA.git /opt/volaura

# Скопируй .env (с локальной машины через SCP)
# gcloud compute scp apps/api/.env volaura-swarm:/opt/volaura/apps/api/.env

# Запусти
cd /opt/volaura
chmod +x infra/start.sh
./infra/start.sh
```

Всё. Brain + Daemon + Health Monitor работают. Telegram шлёт heartbeat.

## Вариант 2: Без GPU VM — используя только cloud API

Если GPU VM дорого ($390/мес сожрёт кредиты за 3 месяца):

1. Возьми дешёвый VPS без GPU: Hetzner CX22 (€3.50/мес) или Oracle Free
2. Brain вместо Gemma4 использует Cerebras API (бесплатный, qwen-3-235b)
3. Daemon уже использует cloud API (Azure, NVIDIA, Cerebras, Groq)

Изменение в brain: заменить `call_gemma4()` на `call_cerebras()`.

## Вариант 3: Локально на твоём компе

Уже работает. `scripts/start_brain_and_daemon.bat`.
Минус: выключишь комп — система спит.

## Что нужно от CEO

| Что | Время | Почему |
|-----|-------|--------|
| Выбрать вариант (1/2/3) | 1 минута | от этого зависит весь деплой |
| Если GCP: создать VM в консоли | 5 минут | я не могу за тебя, нужен браузер |
| SCP .env на VM | 1 минута | секреты не в git |

После этого — система живёт сама. Утренний дайджест в Telegram.
