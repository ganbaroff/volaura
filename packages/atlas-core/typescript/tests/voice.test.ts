/**
 * Voice validator tests — node:test runner, 5 rule-coverage cases.
 *
 * Run with: node --loader ts-node/esm --test tests/voice.test.ts
 * (or ported to Vitest when the monorepo wires it up)
 */
import { strict as assert } from "node:assert";
import { test } from "node:test";
import { validateVoice } from "../src/voice.js";

test("clean storytelling passes", () => {
  const text =
    "Слышу. Пошёл делать миграцию — MIN(uuid) в Postgres не существует, " +
    "переписал на ORDER BY + LIMIT 1.\n\n" +
    "Запушу за пять минут.";
  const result = validateVoice(text);
  assert.equal(result.passed, true);
  assert.deepEqual(result.breaches, []);
});

test("bold-headers breach", () => {
  const text =
    "**Статус:** хорошо\n**Что сделано:** всё\n**Следующее:** жду\n";
  const result = validateVoice(text);
  const types = result.breaches.map((b) => b.type);
  assert.ok(types.includes("bold-headers-in-chat"));
});

test("bullet-wall breach", () => {
  const text =
    "Сделал:\n- прочитал\n- обновил\n- починил\n- запушил\n";
  const result = validateVoice(text);
  const types = result.breaches.map((b) => b.type);
  assert.ok(types.includes("bullet-wall"));
});

test("markdown-heading breach", () => {
  const text = "## Status\n\nВсё ок";
  const result = validateVoice(text);
  const types = result.breaches.map((b) => b.type);
  assert.ok(types.includes("markdown-heading"));
});

test("markdown-table breach", () => {
  const text =
    "Таблица:\n\n| Col | Val |\n| --- | --- |\n| a | b |\n";
  const result = validateVoice(text);
  const types = result.breaches.map((b) => b.type);
  assert.ok(types.includes("markdown-table-in-conversation"));
});

test("trailing-question breach", () => {
  const text = "Проверил всё. Запускать деплой?";
  const result = validateVoice(text);
  const types = result.breaches.map((b) => b.type);
  assert.ok(types.includes("trailing-question-on-reversible"));
});

test("banned-opener breach", () => {
  const text = "Готово. Вот что я сделал: всё работает.";
  const result = validateVoice(text);
  const types = result.breaches.map((b) => b.type);
  assert.ok(types.includes("banned-opener"));
});
