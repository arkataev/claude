#!/usr/bin/env bash
# Install the flow (global CLAUDE.md, skills, agents) from a checkout into ~/.claude on a runner,
# the same layout the links give on the laptop.
set -euo pipefail

flow="$1"
mkdir -p ~/.claude/agents ~/.claude/skills
cp "$flow"/agents/*.md ~/.claude/agents/
cp "$flow/CLAUDE.md" ~/.claude/CLAUDE.md
for dir in "$flow"/*/; do
  name="$(basename "$dir")"
  [ -f "$dir/SKILL.md" ] && cp -R "$dir" ~/.claude/skills/"$name"
done
echo "agents: $(ls ~/.claude/agents | wc -l), skills: $(ls ~/.claude/skills | wc -l)"
