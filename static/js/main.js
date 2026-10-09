/* Otto.web v3. Без JS всё видно и работает; JS добавляет анимации и отправку формы на месте. */
(function () {
  "use strict";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* меню на телефоне */
  var burger = $(".burger"), nav = $("#nav");
  if (burger && nav) {
    var openLabel = burger.getAttribute("aria-label");
    var setMenu = function (open) {
      nav.classList.toggle("open", open);
      burger.setAttribute("aria-expanded", String(open));
      burger.setAttribute("aria-label", open ? burger.dataset.close : openLabel);
    };
    burger.addEventListener("click", function () { setMenu(!nav.classList.contains("open")); });
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) setMenu(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") setMenu(false); });
  }

  /* 1-й момент: уведомления приходят на экран блокировки одно за другим */
  var notifs = $$(".notif");
  if (notifs.length && !reduce) {
    var k = 0, timer;
    var step = function () {
      if (k < notifs.length) { notifs[k].classList.add("is-in"); k++; timer = setTimeout(step, 1400); }
      else { timer = setTimeout(function () { notifs.forEach(function (n) { n.classList.remove("is-in"); }); k = 0; timer = setTimeout(step, 700); }, 3200); }
    };
    timer = setTimeout(step, 500);
    document.addEventListener("visibilitychange", function () {
      clearTimeout(timer);
      if (document.hidden) notifs.forEach(function (n) { n.classList.add("is-in"); });
      else { k = notifs.length; timer = setTimeout(step, 1500); }
    });
  } else {
    notifs.forEach(function (n) { n.classList.add("is-in"); });
  }

  /* главная кнопка: скролл к форме и курсор в поле «Имя» */
  $$("[data-focus]").forEach(function (a) {
    a.addEventListener("click", function () {
      var el = $(a.dataset.focus);
      if (el) setTimeout(function () { el.focus({ preventScroll: true }); }, reduce ? 0 : 650);
    });
  });

  /* нижняя панель на телефоне: появляется после первого экрана, чтобы не закрывать hero */
  var mbar = $(".mbar"), hero = $(".hero");
  if (mbar && hero && "IntersectionObserver" in window) {
    mbar.classList.add("is-hidden");
    new IntersectionObserver(function (en) { mbar.classList.toggle("is-hidden", en[0].isIntersecting); }, { threshold: 0.15 }).observe(hero);
  }

  /* До / След: ползунок */
  $$(".ba-stage").forEach(function (st) {
    var r = $(".ba-range", st);
    var set = function () { st.style.setProperty("--pos", r.value + "%"); };
    r.addEventListener("input", set);
    set();
  });

  /* форма заявки: fetch + ошибки у полей */
  $$("form.leadf").forEach(function (f) {
    var status = $(".lead-status", f), btn = $("button[type=submit]", f), label = btn.textContent;
    var setErr = function (name, msg) {
      var el = f.elements[name], box = el && document.getElementById(el.id + "-err");
      if (!el) return;
      el.setAttribute("aria-invalid", msg ? "true" : "false");
      if (box) box.textContent = msg || "";
    };
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var name = f.elements.name.value.trim(), phone = f.elements.phone.value.replace(/\D/g, "");
      setErr("name", name.length < 2 ? f.dataset.errName : "");
      setErr("phone", phone.length < 6 ? f.dataset.errPhone : "");
      if (name.length < 2) { f.elements.name.focus(); return; }
      if (phone.length < 6) { f.elements.phone.focus(); return; }
      btn.disabled = true; btn.textContent = f.dataset.sending; status.className = "lead-status"; status.textContent = "";
      fetch(f.action, { method: "POST", body: new FormData(f), headers: { Accept: "application/json" } })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (res) {
          if (res.ok) {
            f.classList.add("is-done");
            status.className = "lead-status ok"; status.textContent = f.dataset.ok;
            if (window.umami) window.umami.track("lead", { source: f.elements.source.value });
            return;
          }
          var errs = (res.j && res.j.errors) || {};
          if (errs.name) setErr("name", f.dataset.errName);
          if (errs.phone) setErr("phone", f.dataset.errPhone);
          if (errs.form) status.textContent = f.dataset.errRate;
        })
        .catch(function () { status.textContent = f.dataset.errNet; })
        .then(function () { btn.disabled = false; btn.textContent = label; });
    });
  });

  /* калькулятор на /ceni/ */
  var calc = $("#calc");
  if (calc) {
    var q = new URLSearchParams(location.search).get("p");
    if (q && calc.elements.pkg[q]) calc.elements.pkg[q].checked = true;
    var out = function () {
      var sum = Number((calc.querySelector("[name=pkg]:checked") || {}).value || 0);
      $$("[name=extra]:checked", calc).forEach(function (x) { sum += Number(x.value); });
      var care = calc.elements.care.checked ? 15 : 0;
      $("#sum-once").textContent = sum + " €";
      $("#sum-month").textContent = care + " €";
      var pkg = calc.querySelector("[name=pkg]:checked");
      var extras = $$("[name=extra]:checked", calc).map(function (x) { return x.dataset.name; });
      var msg = (pkg ? pkg.dataset.name : "") + (extras.length ? " + " + extras.join(", ") : "") + (care ? " + 15 €/m" : "") + " = " + sum + " €";
      var field = $("#calc-lead-message");
      if (field) field.value = msg;
    };
    calc.addEventListener("change", out);
    out();
  }

  /* GSAP: reveal, 2-й момент (пин-шоурил), 3-й момент (таймлайн) */
  function motion() {
    if (reduce || !window.gsap || !window.ScrollTrigger) return;
    var gsap = window.gsap;
    gsap.registerPlugin(window.ScrollTrigger);

    // reveal: класс ставим только тем, кто ниже первого экрана, чтобы hero не мигал
    var groups = new Map();
    $$("[data-r]").forEach(function (el) {
      if (el.getBoundingClientRect().top < window.innerHeight * 0.9) return;
      var key = el.parentElement;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(el);
      el.classList.add("r-pre");
    });
    groups.forEach(function (els, parent) {
      window.ScrollTrigger.create({
        trigger: parent, start: "top 85%", once: true,
        onEnter: function () {
          gsap.to(els, { opacity: 1, y: 0, duration: 0.35, ease: "power2.out", stagger: 0.06,
            clearProps: "opacity,transform", onComplete: function () { els.forEach(function (e) { e.classList.remove("r-pre"); }); } });
        }
      });
    });

    var mm = gsap.matchMedia();
    mm.add("(min-width: 900px)", function () {
      var pin = $(".reel-pin"), track = $(".reel-track");
      if (!pin || !track) return;
      var dist = function () { return track.scrollWidth - window.innerWidth; };
      gsap.to(track, {
        x: function () { return -dist(); }, ease: "none",
        scrollTrigger: { trigger: pin, start: "center center", end: function () { return "+=" + dist(); },
          pin: true, scrub: 0.6, invalidateOnRefresh: true, anticipatePin: 1 }
      });
    });
    mm.add("(min-width: 861px)", function () {
      var fill = $(".tl-fill");
      if (fill) gsap.fromTo(fill, { scaleX: 0 }, { scaleX: 1, ease: "none", scrollTrigger: { trigger: ".tl", start: "top 75%", end: "bottom 60%", scrub: 0.5 } });
    });
    mm.add("(max-width: 860px)", function () {
      var fill = $(".tl-fill");
      if (fill) gsap.fromTo(fill, { scaleY: 0 }, { scaleY: 1, ease: "none", scrollTrigger: { trigger: ".tl", start: "top 70%", end: "bottom 55%", scrub: 0.5 } });
    });
  }
  if (document.readyState === "complete") motion();
  else window.addEventListener("load", motion);
})();
