# claude-video-effects · `/effects`

Один клип → 7 разных монтажей. Каждый — одна команда `/effects` в Claude Code.
Без монтажки, без таймлайна. Ты смотришь превью и одобряешь каждый кадр.

## Установка

```bash
git clone https://github.com/maridurmanova/claude-video-effects ~/.claude/skills/effects
pip install -r ~/.claude/skills/effects/requirements.txt
```

Нужны Python 3.10+ и ffmpeg (`brew install ffmpeg`).
При первом запуске один раз скачается модель, которая вырезает человека из кадра (~170 МБ).

## Как пользоваться

Закинь видео в Claude Code и напиши:

```
/effects glass-widgets
```

Claude сначала покажет 2–3 кадра-превью, после твоего «да» отрендерит весь ролик.

| команда | что получится |
|---|---|
| `/effects glass-widgets` | стеклянные виджеты вокруг тебя: счётчик, рендер, профиль, график, 4K — за головой |
| `/effects documentary` | док-серия: ч/б, розовое свечение и титр за головой, плашка с именем, клик «Подписаться» |
| `/effects orbit` | мини-рилс летают вокруг тебя, уходя за спину |
| `/effects chart-split` | сверху растёт график просмотров, снизу ты |
| `/effects spotlight` | тёмная комната, прожектор, неоновое слово загорается за головой |
| `/effects checklist` | стеклянная карточка: Claude по шагам отмечает, что смонтировал |
| `/effects timeline` | над тобой окно монтажки, рендер идёт вживую |
| `/effects reel` | шоу-рилс «один клип → 7 монтажей» с музыкой и звуками интерфейса, без голоса |

Без Claude, вручную:

```bash
cd ~/.claude/skills/effects
python3 run.py list
python3 run.py glass-widgets my_clip.mp4 --preview 1,2.5,5     # кадры на одобрение
python3 run.py glass-widgets my_clip.mp4 -o glass.mp4          # весь ролик, голос сохраняется
python3 run.py orbit my_clip.mp4 --no-voice --music            # только музыка и звуки
python3 reel.py my_clip.mp4 -o reel.mp4                        # шоу-рилс со всеми эффектами
```

## Свои тексты

Имя, @ник и строка серии — в `config.json`. Весь текст на экране лежит в начале каждого файла `effects/*.py`.

## Что внутри

- `effects/` — по файлу на эффект, у каждого `render(ctx, t, source_time)` и список звуков `SFX`
- `lib/segment.py` — маска человека на каждый кадр (текст и карточки «за головой»)
- `lib/ui.py` — интерфейс чата: набор команды, точечное «проявление», наезд на весь экран
- `lib/audio.py` — музыка и звуки синтезируются кодом, никаких лицензий на треки
- шрифты Oswald, Playfair Display, Montserrat, JetBrains Mono (SIL OFL)

Вертикаль 1080×1920, 30 fps, звук −14 LUFS.

---
Сделано с Claude · [@maria.aiart](https://instagram.com/maria.aiart)
