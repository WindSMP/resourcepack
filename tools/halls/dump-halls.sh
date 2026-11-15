#!/usr/bin/env bash
# Regenerates assets/golbg (the dialog engine's hall font + background tiles) and assets/windsmp/layout
# from the GUI-Design-v3 prototype jar, by running the prototype's own drawing code (HallArt.buildPack) headlessly.
#
#   tools/halls/dump-halls.sh /path/to/DialogStore-1.0.0.jar
#
# Needs a JDK (25 was used) and the Gradle cache with paper-api 26.2 and kotlin-stdlib 2.3.21
# (any machine that has built the prototype). Set CP to override the library classpath.
set -euo pipefail
JAR=$(realpath "$1")
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
C=${GRADLE_CACHE:-$HOME/.gradle/caches/modules-2/files-2.1}
if [ -z "${CP:-}" ]; then
  CP=$(find "$C/io.papermc.paper/paper-api/26.2.build.135-stable" "$C/org.jetbrains.kotlin/kotlin-stdlib/2.3.21" -name '*.jar' ! -name '*sources*' | paste -sd:)
  for p in "net.kyori/*/5.2.0" "net.kyori/examination-*/*" "net.kyori/option/*" "com.google.guava/guava/33.6.0-jre" \
           "com.google.guava/failureaccess/*" "com.google.code.gson/gson/2.14.0" "org.yaml/snakeyaml/2.2" "org.joml/joml/1.10.8" \
           "it.unimi.dsi/fastutil/8.5.18" "org.slf4j/slf4j-api/2.0.17" "org.apache.logging.log4j/log4j-api/2.26.0" \
           "org.jspecify/jspecify/1.0.0" "org.jetbrains/annotations/*" "net.md-5/bungeecord-chat/*" "com.mojang/brigadier/1.3.10"; do
    for d in $(ls -d $C/$p 2>/dev/null); do
      f=$(find "$d" -name '*.jar' ! -name '*sources*' ! -name '*javadoc*' | head -1); [ -n "$f" ] && CP=$CP:$f
    done
  done
fi
OUT=$(mktemp -d); trap 'rm -rf "$OUT"' EXIT
javac -d "$OUT/classes" -cp "$CP:$JAR" "$HERE/stub/org/bukkit/inventory/ItemStack.java" "$HERE/DumpHalls.java"
java -Djava.awt.headless=true -cp "$OUT/classes:$CP:$JAR" DumpHalls "$OUT/halls.zip"
rm -rf "$REPO/assets/golbg"
(cd "$OUT" && mkdir x && cd x && unzip -q ../halls.zip && cp -r assets/golbg "$REPO/assets/")
mkdir -p "$REPO/assets/windsmp/layout/duels" "$REPO/assets/windsmp/layout/store"
unzip -p "$JAR" duels/layout.json > "$REPO/assets/windsmp/layout/duels/layout.json"
unzip -p "$JAR" store/glyphs.json > "$REPO/assets/windsmp/layout/store/glyphs.json"
echo "done: assets/golbg, assets/windsmp/layout"
