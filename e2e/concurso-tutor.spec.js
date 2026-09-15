const { test, expect } = require('@playwright/test');

const PASSWORD = process.env.E2E_PASSWORD || 'Ct-E2E-2026!';
const PROFILES = [
  { id: 51, slug: 'pf-admin', label: 'PF Agente Administrativo' },
  { id: 52, slug: 'tecnico-enfermagem', label: 'Técnico em Enfermagem' },
  { id: 53, slug: 'eptc-medio', label: 'EPTC Porto Alegre — Nível Médio' },
  { id: 54, slug: 'eptc-enfermagem-trabalho', label: 'EPTC — Técnico de Enfermagem do Trabalho' },
  { id: 55, slug: 'alvorada-tecnico-enfermagem', label: 'Alvorada 2026 — Técnico em Enfermagem' },
  { id: 56, slug: 'alvorada-auxiliar-administrativo', label: 'Alvorada 2026 — Auxiliar Administrativo' },
];

function creds(profile) {
  return {
    username: `ct_e2e_${profile.id}`,
    password: PASSWORD,
    fullName: `E2E ${profile.label}`,
  };
}

async function measured(timings, name, fn) {
  const start = Date.now();
  const result = await fn();
  timings[name] = Date.now() - start;
  return result;
}

async function openClean(page, timings = {}) {
  await measured(timings, 'pagina_inicial_ms', async () => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#login')).toBeVisible();
  });
  await page.evaluate(() => localStorage.clear());
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(page.locator('#login')).toBeVisible();
  await expect.poll(async () => page.locator('#cadTrilha option').count()).toBeGreaterThanOrEqual(6);
}

async function ensureAccount(page, request, profile, timings = {}) {
  const user = creds(profile);
  await openClean(page, timings);

  const probe = await request.post('/api/login', {
    data: { username: user.username, password: user.password },
  });

  if (!probe.ok()) {
    await page.locator('#cadNome').fill(user.fullName);
    await page.locator('#cadUsuario').fill(user.username);
    await page.locator('#cadSenha').fill(user.password);
    await page.locator('#cadTrilha').selectOption(String(profile.id));
    await page.locator('#cadTempo').selectOption('60');

    await measured(timings, 'cadastro_ms', async () => {
      await page.locator('#btnCadastro').click();
      await expect(page.locator('#cadastroMsg')).toContainText('Perfil criado');
    });
  }

  await page.locator('#username').fill(user.username);
  await page.locator('#password').fill(user.password);

  await measured(timings, 'login_ate_bloco_ms', async () => {
    await page.locator('#btnLogin').click();
    await expect(page.locator('#app')).toBeVisible();
    await expect(page.locator('#formBloco .q').first()).toBeVisible({ timeout: 20_000 });
  });

  await expect.poll(async () => page.evaluate(() => Number(localStorage.getItem('ct_concurso')))).toBe(profile.id);
  await expect(page.locator('#userinfo')).toContainText(user.fullName);
  return user;
}

async function questionIds(page) {
  return page.locator('#formBloco .q').evaluateAll(nodes => nodes.map(node => {
    const input = node.querySelector('input[name^="q"]');
    return input ? Number(input.name.slice(1)) : null;
  }).filter(Number.isFinite));
}

async function answerAll(page, timings) {
  const questions = page.locator('#formBloco .q');
  const count = await questions.count();
  expect(count).toBeGreaterThan(0);

  await measured(timings, 'preencher_respostas_ms', async () => {
    for (let i = 0; i < count; i += 1) {
      const q = questions.nth(i);
      const options = q.locator('.bubble-option');
      if (await options.count()) {
        await options.first().click();
      } else {
        const numeric = q.locator('.numeric-answer');
        if (await numeric.count()) await numeric.fill('1');
      }
    }
  });

  return count;
}

async function submitAnswers(page, expectedCount, timings) {
  const response = await measured(timings, 'envio_e_feedback_ms', async () => {
    const responsePromise = page.waitForResponse(r =>
      r.url().includes('/api/bloco/responder') && r.request().method() === 'POST'
    );
    await page.getByRole('button', { name: 'Enviar respostas' }).click();
    const r = await responsePromise;
    expect(r.ok(), `POST /api/bloco/responder retornou ${r.status()}`).toBeTruthy();
    await expect.poll(async () => page.locator('.submitted-feedback').count()).toBe(expectedCount);
    return r;
  });

  const body = await response.json();
  expect(Array.isArray(body.resultados)).toBeTruthy();
  expect(body.resultados.length).toBe(expectedCount);
  await expect(page.locator('#resultado')).not.toContainText('Não foi possível');
  await expect(page.locator('#resultado')).toContainText('corretas');
  return body;
}

async function loadNextBlock(page, timings) {
  let body;
  await measured(timings, 'mais_questoes_ms', async () => {
    const responsePromise = page.waitForResponse(r =>
      r.url().includes('/api/bloco/proximo') && r.request().method() === 'GET'
    );
    await page.locator('#btnMaisQuestoes').click();
    const response = await responsePromise;
    expect(response.ok(), `GET /api/bloco/proximo retornou ${response.status()}`).toBeTruthy();
    body = await response.json();
    expect(body.bloco).toBeTruthy();
    expect(body.bloco.questoes.length).toBeGreaterThan(0);
    await expect.poll(async () => page.locator('#formBloco .q').count()).toBe(body.bloco.questoes.length);
  });

  const visibleIds = await questionIds(page);
  expect(visibleIds).toEqual(body.bloco.questoes.map(q => Number(q.id)));
  return visibleIds;
}

async function exerciseTabs(page, timings) {
  await measured(timings, 'abrir_boletim_ms', async () => {
    await page.locator('[data-tab="progresso"]').click();
    await expect(page.locator('#tab-progresso')).toBeVisible();
    await expect(page.locator('#dashboardCards .dashboard-card')).toHaveCount(6);
  });

  await measured(timings, 'abrir_plano_ms', async () => {
    await page.locator('[data-tab="plano"]').click();
    await expect(page.locator('#tab-plano')).toBeVisible();
    await expect.poll(async () => page.locator('#planoLista .agenda-item, #planoLista .agenda-empty').count()).toBeGreaterThan(0);
  });

  await measured(timings, 'voltar_bloco_ms', async () => {
    await page.locator('[data-tab="hoje"]').click();
    await expect(page.locator('#tab-hoje')).toBeVisible();
  });
}

async function logout(page, timings) {
  await measured(timings, 'logout_ms', async () => {
    await page.locator('#logout').click();
    await expect(page.locator('#login')).toBeVisible();
    await expect(page.locator('#app')).toBeHidden();
  });
  await expect(page.locator('#formBloco .q')).toHaveCount(0);
  await expect.poll(async () => page.evaluate(() => localStorage.getItem('ct_token'))).toBeNull();
}

for (const profile of PROFILES) {
  test(`${profile.id} · ${profile.label} · jornada completa`, async ({ page, request }, testInfo) => {
    const timings = { profile_id: profile.id, profile: profile.label };
    const pageErrors = [];
    const serverErrors = [];

    page.on('pageerror', err => pageErrors.push(err.message));
    page.on('response', response => {
      if (response.status() >= 500 && response.url().includes('concurso-tutor.vercel.app')) {
        serverErrors.push(`${response.status()} ${response.request().method()} ${response.url()}`);
      }
    });

    await ensureAccount(page, request, profile, timings);
    const firstIds = await questionIds(page);
    expect(firstIds.length).toBeGreaterThan(0);

    const answered = await answerAll(page, timings);
    await submitAnswers(page, answered, timings);
    const nextIds = await loadNextBlock(page, timings);

    if ([51, 52, 55, 56].includes(profile.id)) {
      const overlap = firstIds.filter(id => nextIds.includes(id));
      expect(overlap, 'Perfis com banco suficiente devem priorizar questões inéditas').toEqual([]);
    }

    await exerciseTabs(page, timings);
    await logout(page, timings);

    expect(pageErrors, 'Erros JavaScript não tratados').toEqual([]);
    expect(serverErrors, 'Respostas HTTP 5xx').toEqual([]);

    await testInfo.attach('timings.json', {
      body: JSON.stringify({ ...timings, primeira_lista: firstIds, proxima_lista: nextIds }, null, 2),
      contentType: 'application/json',
    });
  });
}

test('isolamento · troca rápida PF → Técnico em Enfermagem não contamina o bloco', async ({ page, request }, testInfo) => {
  const pf = PROFILES[0];
  const enf = PROFILES[1];
  const timings = {};

  await ensureAccount(page, request, pf, {});
  await logout(page, {});
  await ensureAccount(page, request, enf, {});
  await logout(page, {});

  await openClean(page, {});
  const pfUser = creds(pf);
  const enfUser = creds(enf);

  await page.locator('#username').fill(pfUser.username);
  await page.locator('#password').fill(pfUser.password);
  await page.locator('#btnLogin').click();
  await expect(page.locator('#app')).toBeVisible();

  await measured(timings, 'troca_sessao_ms', async () => {
    await page.locator('#logout').click();
    await expect(page.locator('#login')).toBeVisible();
    await page.locator('#username').fill(enfUser.username);
    await page.locator('#password').fill(enfUser.password);
    await page.locator('#btnLogin').click();
    await expect(page.locator('#formBloco .q').first()).toBeVisible({ timeout: 20_000 });
    await page.waitForTimeout(1200);
  });

  await expect.poll(async () => page.evaluate(() => Number(localStorage.getItem('ct_concurso')))).toBe(enf.id);
  await expect(page.locator('#userinfo')).toContainText(enfUser.fullName);

  const count = await answerAll(page, timings);
  const submission = await submitAnswers(page, count, timings);
  expect(submission.resultados.length).toBe(count);
  await expect(page.locator('#resultado')).not.toContainText('Questão não pertence ao perfil selecionado');

  await testInfo.attach('race-timings.json', {
    body: JSON.stringify(timings, null, 2),
    contentType: 'application/json',
  });
});
