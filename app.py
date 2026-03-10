import streamlit as st
from PIL import Image
from plate_generator import generate_plate
from test_logic import detect_colorblindness
from correction import daltonize
from acuity_generator import generate_acuity_image, screen_ppi, snellen_px
from acuity_logic import AcuityTest, CHART, TOTAL
import os

st.set_page_config(
    page_title="VisionIQ — Eye Health Suite",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
def load_css(path):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">',
    unsafe_allow_html=True
)

# ── Session helpers ───────────────────────────────────────────────────────────
def ss(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

ss("page",             "home")
ss("cb_result",        None)
# Acuity
ss("acuity_step",      "calibrate")   # calibrate | test | result
ss("acuity_screen_in", 15.6)
ss("acuity_w_px",      1920)
ss("acuity_h_px",      1080)
ss("acuity_engine",    None)          # AcuityTest instance
ss("acuity_img",       None)
ss("acuity_attempt",   1)             # 1 or 2 (best of 2 per line shown to user)


def init_engine():
    engine = AcuityTest()
    engine.start()
    st.session_state["acuity_engine"]  = engine
    st.session_state["acuity_attempt"] = 1
    _refresh_image()


def _refresh_image():
    engine = st.session_state["acuity_engine"]
    info   = engine.current_level()
    letters = engine.current_letters()
    img = generate_acuity_image(
        letters,
        info["denom"],
        st.session_state["acuity_screen_in"],
        st.session_state["acuity_w_px"],
        st.session_state["acuity_h_px"],
    )
    st.session_state["acuity_img"] = img


def reset_acuity():
    st.session_state["acuity_step"]   = "calibrate"
    st.session_state["acuity_engine"] = None
    st.session_state["acuity_img"]    = None


# ══════════════════════════════════════════════════════════════════════════════
#  HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="position:relative;overflow:hidden;padding:72px 0 44px;text-align:center;
  background:radial-gradient(ellipse 70% 60% at 50% 0%,rgba(108,99,255,.18),transparent 70%),
             radial-gradient(ellipse 40% 40% at 80% 80%,rgba(255,101,132,.10),transparent 60%),#05050a">
  <div style="display:inline-block;font-size:11px;font-weight:500;letter-spacing:3px;
    text-transform:uppercase;color:#43e8b0;border:1px solid rgba(67,232,176,.3);
    border-radius:100px;padding:6px 18px;margin-bottom:22px">✦ Binary Search Acuity Engine</div>
  <h1 style="font-family:'Syne',sans-serif;font-size:clamp(34px,6vw,64px);font-weight:800;
    line-height:1.0;letter-spacing:-2px;color:#fff;margin-bottom:14px">
    Know Your<br>
    <span style="background:linear-gradient(135deg,#6c63ff,#ff6584);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">Vision.</span>
  </h1>
  <p style="font-size:15px;font-weight:300;color:#6b6b8a;max-width:440px;margin:0 auto;line-height:1.7">
    Clinical binary-search Snellen test with screen calibration.<br>
    Result in 4–6 rows instead of 12.
  </p>
</div>
""", unsafe_allow_html=True)

# ── NAV ───────────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2, gap="medium")
with c1:
    st.markdown("""
    <div style="background:#111120;border:1px solid rgba(255,255,255,.07);border-radius:18px;padding:24px;margin-bottom:8px">
      <div style="font-size:30px;margin-bottom:10px">🎨</div>
      <div style="font-family:'Syne',sans-serif;font-size:16px;font-weight:700;color:#fff;margin-bottom:4px">Color Blindness Test</div>
      <div style="font-size:13px;color:#6b6b8a;line-height:1.5;margin-bottom:12px">Ishihara plates detect red-green and other color deficiencies.</div>
      <span style="font-size:11px;padding:3px 10px;border-radius:100px;background:rgba(108,99,255,.15);color:#6c63ff;border:1px solid rgba(108,99,255,.3)">Ishihara Method</span>
    </div>""", unsafe_allow_html=True)
    if st.button("Start Color Test →", key="go_color"):
        st.session_state["page"] = "color"
        st.rerun()

with c2:
    st.markdown("""
    <div style="background:#111120;border:1px solid rgba(255,255,255,.07);border-radius:18px;padding:24px;margin-bottom:8px">
      <div style="font-size:30px;margin-bottom:10px">👁️</div>
      <div style="font-family:'Syne',sans-serif;font-size:16px;font-weight:700;color:#fff;margin-bottom:4px">Visual Acuity Test</div>
      <div style="font-size:13px;color:#6b6b8a;line-height:1.5;margin-bottom:12px">Binary-search Snellen with real diopter estimates. Done in ~5 rows.</div>
      <span style="font-size:11px;padding:3px 10px;border-radius:100px;background:rgba(67,232,176,.1);color:#43e8b0;border:1px solid rgba(67,232,176,.25)">Binary Search Engine</span>
    </div>""", unsafe_allow_html=True)
    if st.button("Start Acuity Test →", key="go_acuity"):
        st.session_state["page"] = "acuity"
        st.rerun()

st.markdown('<hr style="border:none;height:1px;background:rgba(255,255,255,.07);margin:8px 0 0">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: COLOR BLINDNESS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["page"] == "color":

    os.makedirs("plates", exist_ok=True)
    generate_plate("12", (200, 255, 200), (180, 0, 0),   "plates/normal.png")
    generate_plate("8",  (200, 240, 240), (200, 200, 0), "plates/protanopia.png")
    generate_plate("5",  (240, 200, 200), (0, 180, 0),   "plates/deuteranopia.png")
    plates = [
        ("plates/normal.png",      "12", "Normal Vision"),
        ("plates/protanopia.png",  "8",  "Protanopia"),
        ("plates/deuteranopia.png","5",  "Deuteranopia"),
    ]

    st.markdown("""
    <div style="padding:32px 0 8px">
      <p style="font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#6c63ff;font-weight:500">Color Vision Test</p>
      <h2 style="font-family:'Syne',sans-serif;font-size:26px;font-weight:700;color:#fff;margin:6px 0">Ishihara Plate Test</h2>
      <p style="font-size:14px;color:#6b6b8a">Look at each plate and type the hidden number within 3 seconds.</p>
    </div>
    <div style="background:linear-gradient(135deg,rgba(67,232,176,.05),rgba(108,99,255,.05));
      border:1px solid rgba(67,232,176,.18);border-radius:14px;padding:18px 22px;margin:12px 0 24px">
      <div style="font-family:'Syne',sans-serif;font-size:13px;font-weight:700;color:#43e8b0;margin-bottom:10px">📋 Instructions</div>
      <div style="display:flex;flex-direction:column;gap:7px;font-size:13px;color:#6b6b8a">
        <div>→ &nbsp;Sit <strong style="color:#c8c8e0">50–60 cm</strong> from screen in a well-lit room</div>
        <div>→ &nbsp;<strong style="color:#c8c8e0">Do not zoom in</strong> — normal screen size only</div>
        <div>→ &nbsp;Answer within <strong style="color:#c8c8e0">3 seconds</strong> per plate</div>
        <div>→ &nbsp;Leave blank if you cannot see a number</div>
        <div>→ &nbsp;Remove color-corrective glasses</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    responses = []
    cols = st.columns(3, gap="medium")
    for i, (path, number, label) in enumerate(plates):
        with cols[i]:
            st.markdown(f'<p style="font-size:11px;font-weight:600;color:#6b6b8a;margin-bottom:6px;text-transform:uppercase;letter-spacing:1px">Plate {i+1} — {label}</p>', unsafe_allow_html=True)
            st.image(path, use_container_width=True)
            ans = st.text_input(f"Plate {i+1}", placeholder="Type what you see…", key=f"plate_{i}", label_visibility="collapsed")
            responses.append((ans, number, label))

    if st.button("🔍  Analyze My Color Vision", key="detect_btn"):
        result = detect_colorblindness(responses)
        st.session_state["cb_result"] = result
        icon   = "✅" if result == "Normal Vision" else "⚠️"
        advice = {
            "Normal Vision":  "Normal color vision confirmed. No correction needed.",
            "Protanopia":     "Red-blind deficiency detected. Reds and greens appear similar. Consider EnChroma lenses.",
            "Deuteranopia":   "Green-blind deficiency detected. Reds and greens appear similar. Consult an optometrist.",
        }.get(result, "Consult an eye care professional.")
        st.markdown(f"""
        <div style="background:rgba(108,99,255,.10);border:1px solid rgba(108,99,255,.3);
          border-radius:14px;padding:20px 22px;display:flex;align-items:center;gap:14px;margin-top:18px">
          <div style="width:44px;height:44px;border-radius:50%;flex-shrink:0;
            background:linear-gradient(135deg,#6c63ff,#ff6584);
            display:flex;align-items:center;justify-content:center;font-size:18px">{icon}</div>
          <div>
            <div style="font-size:11px;color:#6b6b8a;letter-spacing:1px;text-transform:uppercase;margin-bottom:2px">Diagnosis</div>
            <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:700;color:#fff">{result}</div>
            <div style="font-size:13px;color:#6b6b8a;margin-top:2px">{advice}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<hr style="border:none;height:1px;background:rgba(255,255,255,.07);margin:28px 0 18px">', unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#ff6584;font-weight:500">Color Correction</p>
    <h3 style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#fff;margin:6px 0 4px">Upload Image for Correction</h3>
    <p style="font-size:13px;color:#6b6b8a;margin-bottom:14px">See any image reprocessed for your specific color vision type.</p>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("Drop image", type=["jpg","jpeg","png"], label_visibility="collapsed")
    if uploaded:
        img = Image.open(uploaded).convert("RGB")
        result = st.session_state.get("cb_result")
        if not result:
            st.info("💡 Run the color vision test above first.")
        elif result != "Normal Vision":
            corrected = daltonize(img, result)
            col_a, col_b = st.columns(2, gap="medium")
            with col_a:
                st.markdown('<p style="font-size:11px;color:#6b6b8a;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Original</p>', unsafe_allow_html=True)
                st.image(img, use_container_width=True)
            with col_b:
                st.markdown('<p style="font-size:11px;color:#43e8b0;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Corrected</p>', unsafe_allow_html=True)
                st.image(corrected, use_container_width=True)
        else:
            st.image(img, use_container_width=True)
            st.success("✅ Normal color vision — no correction needed.")

    st.markdown("<div style='margin-top:22px'>", unsafe_allow_html=True)
    if st.button("← Back to Home", key="back_color"):
        st.session_state["page"] = "home"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: VISUAL ACUITY — BINARY SEARCH ENGINE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state["page"] == "acuity":

    step = st.session_state["acuity_step"]

    # ── STEP: CALIBRATE ──────────────────────────────────────────────────────
    if step == "calibrate":

        st.markdown("""
        <div style="padding:32px 0 8px">
          <p style="font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#43e8b0;font-weight:500">Step 1 of 3 — Screen Calibration</p>
          <h2 style="font-family:'Syne',sans-serif;font-size:26px;font-weight:700;color:#fff;margin:6px 0">Calibrate Your Screen</h2>
          <p style="font-size:14px;color:#6b6b8a;line-height:1.6;max-width:500px">
            We calculate the exact physical size of each letter using your screen specs.
            Without this, results are meaningless. Takes 30 seconds.
          </p>
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns(2, gap="medium")
        with col_a:
            screen_in = st.number_input(
                "Screen size (diagonal inches)",
                min_value=5.0, max_value=100.0,
                value=15.6, step=0.1,
                help="Measure corner to corner of the screen panel only, not the bezel"
            )
            st.caption("Laptop: 13–15.6\"  ·  Monitor: 24–27\"  ·  Phone: 5–7\"")
        with col_b:
            res_map = {
                "1920 × 1080  (Full HD)":        (1920, 1080),
                "2560 × 1440  (2K / QHD)":       (2560, 1440),
                "3840 × 2160  (4K / UHD)":       (3840, 2160),
                "1366 × 768   (HD Laptop)":       (1366, 768),
                "1280 × 800   (Older Laptop)":    (1280, 800),
                "2560 × 1600  (MacBook Pro 13)":  (2560, 1600),
                "2880 × 1800  (MacBook Pro 16)":  (2880, 1800),
                "1920 × 1200  (WUXGA)":           (1920, 1200),
            }
            res_choice     = st.selectbox("Screen resolution", list(res_map.keys()))
            w_px, h_px     = res_map[res_choice]

        import math
        ppi = screen_ppi(screen_in, w_px, h_px)
        sample_px = snellen_px(20, screen_in, w_px, h_px)

        col_ppi, col_sample = st.columns(2, gap="medium")
        with col_ppi:
            quality = "✅ Good" if 80 < ppi < 450 else "⚠️ Check screen size"
            st.markdown(f"""
            <div style="background:rgba(108,99,255,.08);border:1px solid rgba(108,99,255,.2);
              border-radius:12px;padding:14px 16px;margin-top:8px">
              <div style="font-size:11px;color:#6b6b8a;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">Screen Density</div>
              <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#fff">{ppi:.0f} PPI</div>
              <div style="font-size:12px;color:#6b6b8a;margin-top:3px">{quality}</div>
            </div>""", unsafe_allow_html=True)
        with col_sample:
            st.markdown(f"""
            <div style="background:rgba(67,232,176,.06);border:1px solid rgba(67,232,176,.2);
              border-radius:12px;padding:14px 16px;margin-top:8px">
              <div style="font-size:11px;color:#6b6b8a;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">20/20 Letter Size</div>
              <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#fff">{sample_px}px</div>
              <div style="font-size:12px;color:#6b6b8a;margin-top:3px">At 60cm on your screen</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(67,232,176,.05),rgba(108,99,255,.05));
          border:1px solid rgba(67,232,176,.18);border-radius:14px;padding:18px 22px;margin:20px 0">
          <div style="font-family:'Syne',sans-serif;font-size:13px;font-weight:700;color:#43e8b0;margin-bottom:12px">
            ⚙️ Step 2 — Physical Setup
          </div>
          <div style="display:flex;flex-direction:column;gap:9px;font-size:13px;color:#6b6b8a">
            <div>📏 &nbsp;<strong style="color:#fff">Sit exactly 60 cm from your screen.</strong>
              Arm test: fingertips on screen, elbow should be nearly straight.</div>
            <div>💡 &nbsp;Screen brightness at <strong style="color:#c8c8e0">maximum.</strong> Reduce glare from windows/lamps.</div>
            <div>👓 &nbsp;<strong style="color:#c8c8e0">Remove glasses first</strong> to find natural acuity. Repeat with glasses to compare.</div>
            <div>👁️ &nbsp;<strong style="color:#c8c8e0">Cover left eye with palm</strong> (not fingers). Test right eye first, then swap and retest.</div>
            <div>🚫 &nbsp;<strong style="color:#c8c8e0">No squinting or leaning forward.</strong> If you cannot read it naturally → press Cannot See.</div>
          </div>
        </div>

        <div style="background:rgba(108,99,255,.06);border:1px solid rgba(108,99,255,.2);
          border-radius:14px;padding:16px 20px;margin-bottom:20px">
          <div style="font-family:'Syne',sans-serif;font-size:13px;font-weight:700;color:#6c63ff;margin-bottom:8px">
            🔬 How This Test Works
          </div>
          <div style="font-size:13px;color:#6b6b8a;line-height:1.6">
            Uses a <strong style="color:#c8c8e0">binary search algorithm</strong> — starts in the middle of the chart (20/40),
            jumps up if you pass, down if you fail. Finds your exact threshold in
            <strong style="color:#c8c8e0">4–6 rows</strong> instead of reading all 12 lines top to bottom.
            Each row shows letters <strong style="color:#c8c8e0">twice</strong> — you need to pass at least once to move up.
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✅  Done — Start Eye Test", key="start_acuity"):
            st.session_state["acuity_screen_in"] = screen_in
            st.session_state["acuity_w_px"]      = w_px
            st.session_state["acuity_h_px"]      = h_px
            init_engine()
            st.session_state["acuity_step"]      = "test"
            st.rerun()

        st.markdown("<div style='margin-top:14px'>", unsafe_allow_html=True)
        if st.button("← Back to Home", key="back_calib"):
            st.session_state["page"] = "home"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


    # ── STEP: TEST ───────────────────────────────────────────────────────────
    elif step == "test":

        engine = st.session_state["acuity_engine"]
        if engine is None:
            st.session_state["acuity_step"] = "calibrate"
            st.rerun()

        info    = engine.current_level()
        letters = engine.current_letters()
        attempt = st.session_state["acuity_attempt"]

        # Progress visualisation
        lo_label  = CHART[info["lo"]][0]
        hi_label  = CHART[info["hi"]][0]
        rows_done = len(engine.history)
        st.markdown(f"""
        <div style="margin:12px 0 20px">
          <div style="display:flex;justify-content:space-between;margin-bottom:6px">
            <span style="font-size:12px;color:#6b6b8a">Search range: <strong style="color:#c8c8e0">{lo_label}</strong> → <strong style="color:#c8c8e0">{hi_label}</strong></span>
            <span style="font-size:12px;color:#6c63ff;font-weight:600">{rows_done} rows read</span>
          </div>
          <div style="height:4px;background:rgba(255,255,255,.07);border-radius:2px">
            <div style="height:4px;width:{min(95, rows_done*16)}%;
              background:linear-gradient(90deg,#6c63ff,#43e8b0);border-radius:2px"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Current row info
        st.markdown(f"""
        <div style="background:#111120;border:1px solid rgba(255,255,255,.07);
          border-radius:14px;padding:16px 20px;margin-bottom:14px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
            <div style="display:flex;align-items:center;gap:10px">
              <span style="font-family:'Syne',sans-serif;font-size:15px;font-weight:700;color:#6c63ff">{info['label']}</span>
              <span style="font-size:11px;padding:2px 9px;border-radius:100px;
                background:rgba(108,99,255,.15);color:#6c63ff;border:1px solid rgba(108,99,255,.3)">
                Attempt {attempt}/2
              </span>
            </div>
            <span style="font-size:11px;padding:3px 10px;border-radius:100px;
              background:rgba(67,232,176,.1);color:#43e8b0;border:1px solid rgba(67,232,176,.22)">
              📏 60 cm
            </span>
          </div>
          <div style="font-size:12px;color:#6b6b8a">{info['desc']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Letter image
        if st.session_state["acuity_img"] is not None:
            st.image(st.session_state["acuity_img"], use_container_width=True)

        # Answer input
        ans = st.text_input(
            "Letters you see",
            placeholder="Type the letters (e.g.  D H R S N)…",
            key=f"ans_{info['index']}_{attempt}_{rows_done}"
        )

        col_yes, col_no = st.columns(2, gap="medium")

        with col_yes:
            if st.button("✅  Can See — Submit Answer", key=f"yes_{rows_done}_{attempt}"):
                done = engine.submit_answer(ans)
                if done:
                    st.session_state["acuity_step"]    = "result"
                else:
                    # Check if we moved to a new line or same line (attempt 2)
                    new_info = engine.current_level()
                    if new_info["index"] == info["index"]:
                        st.session_state["acuity_attempt"] = 2
                    else:
                        st.session_state["acuity_attempt"] = 1
                    _refresh_image()
                st.rerun()

        with col_no:
            if st.button("❌  Cannot See This Row", key=f"no_{rows_done}_{attempt}"):
                done = engine.skip_line()
                if done:
                    st.session_state["acuity_step"] = "result"
                else:
                    st.session_state["acuity_attempt"] = 1
                    _refresh_image()
                st.rerun()

        # History trail
        if engine.history:
            trail = '<div style="display:flex;gap:6px;margin-top:16px;flex-wrap:wrap">'
            for h in engine.history:
                color = "#43e8b0" if h["passed"] else "#ff6584"
                trail += f'<span style="font-size:11px;padding:3px 9px;border-radius:100px;background:rgba(0,0,0,.3);color:{color};border:1px solid {color}55">{h["label"]} {h["correct"]}/{h["total"]} {"✓" if h["passed"] else "✗"}</span>'
            trail += '</div>'
            st.markdown(trail, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:20px'>", unsafe_allow_html=True)
        if st.button("← Restart Test", key="restart_mid"):
            reset_acuity()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


    # ── STEP: RESULT ─────────────────────────────────────────────────────────
    elif step == "result":

        engine = st.session_state["acuity_engine"]
        result = engine.get_result() if engine else {"done": False}

        if not result.get("done"):
            st.session_state["acuity_step"] = "calibrate"
            st.rerun()

        advice  = result["advice"]
        color   = advice["color"]
        icon    = {"none":"✅","low":"🟡","moderate":"🟠","high":"⚠️","urgent":"🚨"}.get(advice["urgency"],"👁️")

        st.markdown(f"""
        <div style="padding:28px 0 8px">
          <p style="font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#43e8b0;font-weight:500">Test Complete</p>
          <h2 style="font-family:'Syne',sans-serif;font-size:26px;font-weight:700;color:#fff;margin:6px 0">Your Vision Result</h2>
        </div>
        <div style="background:rgba(0,0,0,.3);border:1px solid {color}40;border-radius:18px;padding:26px;margin-bottom:24px">
          <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px">
            <div style="width:52px;height:52px;border-radius:50%;flex-shrink:0;
              background:linear-gradient(135deg,{color},{color}88);
              display:flex;align-items:center;justify-content:center;font-size:24px">{icon}</div>
            <div>
              <div style="font-size:11px;color:#6b6b8a;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px">Visual Acuity</div>
              <div style="font-family:'Syne',sans-serif;font-size:26px;font-weight:800;color:#fff">{result['label']}</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px">
            <div style="background:rgba(255,255,255,.04);border-radius:12px;padding:14px 16px">
              <div style="font-size:11px;color:#6b6b8a;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">Estimated Prescription</div>
              <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:700;color:{color}">{advice['rx']}</div>
            </div>
            <div style="background:rgba(255,255,255,.04);border-radius:12px;padding:14px 16px">
              <div style="font-size:11px;color:#6b6b8a;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">Category</div>
              <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:700;color:{color}">{advice['category']} {advice['type']}</div>
            </div>
          </div>
          <div style="font-size:14px;color:#c8c8e0;line-height:1.6">{advice['detail']}</div>
        </div>
        """, unsafe_allow_html=True)

        # How binary search found this result
        st.markdown("""
        <p style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:#fff;margin-bottom:10px">
          🔬 How the Binary Search Found Your Result
        </p>
        """, unsafe_allow_html=True)

        for h in result["history"]:
            color_h = "#43e8b0" if h["passed"] else "#ff6584"
            icon_h  = "↑ Jumped up" if h["passed"] else "↓ Jumped down"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;
              border-bottom:1px solid rgba(255,255,255,.04);border-radius:8px">
              <span style="font-family:'Syne',sans-serif;font-weight:700;font-size:13px;
                color:#fff;min-width:60px">{h['label']}</span>
              <span style="font-size:12px;color:{color_h};font-weight:600;min-width:70px">
                {h['correct']}/{h['total']} letters</span>
              <span style="font-size:12px;color:{color_h}">{"✓ Pass — " if h['passed'] else "✗ Fail — "}{icon_h}</span>
            </div>
            """, unsafe_allow_html=True)

        # Full chart reference
        st.markdown("""
        <p style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:#fff;margin:24px 0 10px">
          📊 Full Snellen Reference — Your Result Highlighted
        </p>
        """, unsafe_allow_html=True)

        for i, (label, denom, diopter, desc) in enumerate(CHART):
            is_hl   = (i == result["index"])
            bg_r    = "rgba(108,99,255,.09)" if is_hl else "transparent"
            border  = "1px solid rgba(108,99,255,.4)" if is_hl else "1px solid rgba(255,255,255,.04)"
            rx_txt  = f"{diopter:+.2f} D" if diopter != 0 else "None"
            rx_col  = "#ff6584" if diopter < -1 else ("#ffd000" if diopter < 0 else ("#43e8b0" if diopter == 0 else "#ffa500"))
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:72px 76px 1fr 110px;gap:8px;
              padding:10px 14px;border-radius:8px;border:{border};background:{bg_r};margin-bottom:3px">
              <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:13px;color:#fff">{label}</div>
              <div style="font-size:12px;color:{rx_col};font-weight:600">{rx_txt}</div>
              <div style="font-size:12px;color:{'#e0e0f0' if is_hl else '#6b6b8a'}">{desc}</div>
              <div style="font-size:11px;color:#6c63ff;text-align:right">{"← Your result" if is_hl else ""}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:rgba(255,200,0,.05);border:1px solid rgba(255,200,0,.18);
          border-radius:12px;padding:14px 18px;margin-top:18px">
          <p style="font-size:12px;color:#6b6b8a;line-height:1.6;margin:0">
            ⚠️ <strong style="color:#ffd000">Disclaimer:</strong>
            This is a calibrated screening tool — not a clinical prescription.
            Real prescriptions require a phoropter exam by a licensed optometrist
            who also tests for astigmatism, presbyopia, and binocular balance.
            <strong style="color:#c8c8e0">See an eye care professional before purchasing glasses.</strong>
          </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        col_r, col_b = st.columns(2, gap="medium")
        with col_r:
            if st.button("🔄  Retake Test", key="retake"):
                reset_acuity()
                st.rerun()
        with col_b:
            if st.button("← Back to Home", key="back_result"):
                reset_acuity()
                st.session_state["page"] = "home"
                st.rerun()


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border:none;height:1px;background:rgba(255,255,255,.07);margin:32px 0 0">
<div style="text-align:center;padding:26px 0;color:#6b6b8a;font-size:13px">
  Built with <span style="color:#6c63ff">♥</span> · VisionIQ ·
  <span style="color:#6c63ff">Not a substitute for professional medical advice</span>
</div>
""", unsafe_allow_html=True)