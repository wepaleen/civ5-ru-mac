#!/usr/bin/env bash
#
# Civilization V (macOS, Steam, build 1.4.2) — установка полной русификации.
#
# Что делает:
#   1. достаёт из образа civa5rus (CIV_V_RUS.dmg) кириллический шрифт,
#      текстурный атлас, базовый русский текст и русскую озвучку;
#   2. встраивает их в структуру нового билда (Contents/Assets/Assets);
#   3. накатывает НАШ перевод дополнений (G&K, BNW, DLC) из translations/;
#   4. нормализует символы под шрифт, выставляет язык, чистит кэш.
#
# Образ CIV_V_RUS.dmg в репозиторий НЕ входит (копирайт 2K/Firaxis). Если не
# указать путь к нему, скрипт сам скачает образ с источника civa5rus.
#
# Использование:
#   ./scripts/install.sh                       # сам скачает образ и поставит
#   ./scripts/install.sh /путь/к/CIV_V_RUS.dmg # взять уже скачанный образ
#   ./scripts/install.sh "" "/путь/к/Civilization V.app"  # своя папка игры
#
set -euo pipefail

# образ civa5rus на Яндекс.Диске (https://yadi.sk/d/bcwiMUYF3aHdtg), url-encoded
PUBLIC_KEY_ENC="https%3A%2F%2Fyadi.sk%2Fd%2FbcwiMUYF3aHdtg"
DMG="${1:-}"
DEFAULT_APP="$HOME/Library/Application Support/Steam/steamapps/common/Sid Meier's Civilization V/Civilization V.app"
APP="${2:-$DEFAULT_APP}"
ASSETS="$APP/Contents/Assets/Assets"
RES="$APP/Contents/Assets/Resource"
SUPPORT="$HOME/Library/Application Support/Sid Meier's Civilization 5"
CFG="$SUPPORT/config.ini"
CACHE="$SUPPORT/cache"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
BK="$HOME/civ5_rus_backup"

command -v hdiutil >/dev/null || { echo "✗ нужен hdiutil (macOS)"; exit 1; }
command -v python3 >/dev/null || { echo "✗ нужен python3"; exit 1; }
command -v curl    >/dev/null || { echo "✗ нужен curl"; exit 1; }
[ -d "$ASSETS" ] || { echo "✗ Игра не найдена: $ASSETS"; echo "  Передай путь к .app вторым аргументом."; exit 1; }

# Образ не указан — качаем с civa5rus (повторный запуск дописывает докачкой -C -)
if [ -z "$DMG" ]; then
  DMG="$HOME/civ5_rus_cache/CIV_V_RUS.dmg"
  mkdir -p "$(dirname "$DMG")"
  if [ ! -f "$DMG" ] || [ "$(stat -f%z "$DMG" 2>/dev/null || echo 0)" -lt 3314601393 ]; then
    echo "▸ Образ не указан — качаю с civa5rus (Яндекс.Диск, ~3.1 ГБ)…"
    API="https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=$PUBLIC_KEY_ENC"
    HREF=$(curl -sL "$API" | grep -o '"href": *"[^"]*"' | head -1 | sed 's/"href": *"//; s/"$//')
    [ -n "$HREF" ] || { echo "✗ не удалось получить ссылку. Скачай вручную с http://civa5rus.tilda.ws/ и передай путь аргументом."; exit 1; }
    curl -L --fail -C - -o "$DMG" "$HREF"
  fi
fi
[ -f "$DMG" ] || { echo "✗ Образ не найден: $DMG"; exit 1; }

echo "▸ Монтирую образ…"
MNT="$(mktemp -d)"
hdiutil attach "$DMG" -readonly -nobrowse -noautoopen -mountpoint "$MNT" >/dev/null
trap 'hdiutil detach "$MNT" >/dev/null 2>&1 || true' EXIT
M="$MNT/Home"
[ -d "$M" ] || { echo "✗ В образе нет папки Home — это не CIV_V_RUS.dmg?"; exit 1; }

echo "▸ Бэкап оригиналов → $BK"
mkdir -p "$BK/DX9" "$BK/Fonts"
cp -pn "$RES/DX9/UITextures.fpk" "$BK/DX9/" 2>/dev/null || true
cp -pn "$ASSETS/UI/Fonts/Tw Cent MT/"*.ggxml "$BK/Fonts/" 2>/dev/null || true
[ -f "$CFG" ] && cp -pn "$CFG" "$BK/config.ini" 2>/dev/null || true

echo "▸ 1/5 Кириллический шрифт (ggxml + атлас UITextures.fpk)…"
cp "$M/Assets/UI/Fonts/Tw Cent MT/"*.ggxml "$ASSETS/UI/Fonts/Tw Cent MT/"
cp "$M/Resource/DX9/UITextures.fpk" "$RES/DX9/UITextures.fpk"

echo "▸ 2/5 Базовый русский текст (из образа)…"
cp -R "$M/Assets/Gameplay/XML/NewText/RU_RU" "$ASSETS/Gameplay/XML/NewText/"
cp "$M/Assets/Gameplay/XML/NewText/Russian.xml" "$ASSETS/Gameplay/XML/NewText/"
cp "$M/Assets/Gameplay/XML/NewText/CIV5Credits_RU_RU.txt" "$ASSETS/Gameplay/XML/NewText/" 2>/dev/null || true

echo "▸ 3/5 Русская озвучка (speech)…"
while IFS= read -r d; do
  rel="${d#$M/Assets/}"
  cp -R "$d" "$ASSETS/$(dirname "$rel")/" 2>/dev/null || true
done < <(find "$M/Assets" -type d -iname russian -path "*peech*" 2>/dev/null)

echo "▸ 4/5 Перевод дополнений (наш, G&K/BNW/DLC)…"
cp -R "$HERE/translations/DLC/." "$ASSETS/DLC/"

echo "▸ 5/5 Нормализация под шрифт + язык + кэш…"
python3 "$HERE/scripts/normalize.py" "$ASSETS"
if [ -f "$CFG" ]; then
  /usr/bin/sed -i '' -e 's/^Language = .*/Language = ru_RU/' -e 's/^AudioLanguage = .*/AudioLanguage = ru_RU/' "$CFG"
else
  echo "  ⚠ config.ini не найден — запусти игру один раз, потом перезапусти скрипт (или выставь язык вручную)."
fi
rm -f "$CACHE/Civ5CoreDatabase.db" "$CACHE/Civ5DebugDatabase.db" "$CACHE"/Localization-*.db 2>/dev/null || true

echo "✓ Готово. Запусти игру (первый старт дольше — пересборка текста)."
echo "  Откат: восстанови файлы из $BK и поставь Language = en_US в config.ini."
