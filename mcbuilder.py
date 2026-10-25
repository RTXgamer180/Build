"""
MCBuilder — MCreator-style Minecraft builder for Render.com
Sections:
  • Workspace / Dashboard
  • Java Mod Builder (Forge/NeoForge scaffolding + downloadable project)
  • MCBE Addon Creator (Behavior + Resource packs)
  • Native / DLL Stub Generator (educational C++ template)
Deploy: put this file + requirements.txt on Render as a Web Service.
"""

import streamlit as st
import json
import uuid
import zipfile
import io
import textwrap
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Page config & MCreator-inspired dark theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MCBuilder — Mod & Addon Creator",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS — dark grey + purple accents (inspired by MCreator dark / Prismora)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg: #1e1e1e;
        --panel: #2b2b2b;
        --panel2: #323232;
        --alt: #3a3a3a;
        --fg: #f0f0f0;
        --fg-dim: #b0b0b0;
        --accent: #9b59d0;
        --accent-hover: #b07ce0;
        --accent2: #6c3fa0;
        --success: #4caf50;
        --border: #505050;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: var(--bg) !important;
        color: var(--fg) !important;
    }

    .stApp {
        background-color: var(--bg);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #252525 !important;
        border-right: 1px solid var(--border);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--accent) !important;
    }

    /* Headers */
    h1, h2, h3, h4 {
        color: var(--fg) !important;
    }
    h1 {
        border-bottom: 2px solid var(--accent);
        padding-bottom: 0.3rem;
    }

    /* Buttons */
    .stButton > button {
        background-color: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: background 0.15s;
    }
    .stButton > button:hover {
        background-color: var(--accent-hover) !important;
        color: white !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background-color: var(--accent2) !important;
        color: white !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background-color: var(--alt) !important;
        color: var(--fg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 4px !important;
    }

    /* Cards / expanders */
    .stExpander {
        background-color: var(--panel) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: var(--panel);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: var(--panel);
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: var(--fg-dim);
        border-radius: 6px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--accent) !important;
        color: white !important;
    }

    /* Code blocks */
    .stCodeBlock {
        background-color: #1a1a1a !important;
        border: 1px solid var(--border);
        border-radius: 6px;
    }

    /* Info / success boxes */
    .stAlert {
        background-color: var(--panel2) !important;
        border-left: 4px solid var(--accent) !important;
        color: var(--fg) !important;
    }

    /* Logo header */
    .mcb-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1.5rem;
    }
    .mcb-logo {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #9b59d0, #6c3fa0);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 4px 12px rgba(155, 89, 208, 0.4);
    }
    .mcb-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--fg);
        margin: 0;
    }
    .mcb-sub {
        color: var(--fg-dim);
        font-size: 0.9rem;
        margin: 0;
    }

    /* Element cards */
    .element-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .element-card:hover {
        border-color: var(--accent);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def init_state():
    defaults = {
        "project_name": "MyAwesomeMod",
        "mod_id": "myawesomemod",
        "author": "Creator",
        "version": "1.0.0",
        "mc_version": "1.20.1",
        "java_elements": [],      # list of dicts
        "bedrock_items": [],
        "bedrock_blocks": [],
        "bedrock_entities": [],
        "dll_exports": [],
        "namespace": "myaddon",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def gen_uuid() -> str:
    return str(uuid.uuid4())

def safe_id(name: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name.lower().replace(" ", "_"))

def make_zip(files: dict[str, str | bytes]) -> bytes:
    """files: {path_inside_zip: content_str_or_bytes}"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            if isinstance(content, str):
                content = content.encode("utf-8")
            zf.writestr(path, content)
    buf.seek(0)
    return buf.getvalue()

# ---------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="mcb-header">
        <div class="mcb-logo">🛠️</div>
        <div>
            <p class="mcb-title">MCBuilder</p>
            <p class="mcb-sub">MCreator-style toolkit</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Workspace Sections",
        [
            "🏠 Dashboard",
            "☕ Java Mod Builder",
            "📦 MCBE Addon Creator",
            "🔌 Native / DLL Maker",
            "⚙️ Project Settings",
            "📖 Help & Deploy",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption(f"Project: **{st.session_state.project_name}**")
    st.caption(f"Elements: {len(st.session_state.java_elements)} Java · "
               f"{len(st.session_state.bedrock_items)+len(st.session_state.bedrock_blocks)+len(st.session_state.bedrock_entities)} Bedrock")

# ===========================================================================
# PAGE: DASHBOARD
# ===========================================================================
if page == "🏠 Dashboard":
    st.title("Workspace Dashboard")
    st.markdown("Create Minecraft Java mods, Bedrock addons and native stubs — all from one place.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Java Elements", len(st.session_state.java_elements))
    c2.metric("Bedrock Items", len(st.session_state.bedrock_items))
    c3.metric("Bedrock Blocks", len(st.session_state.bedrock_blocks))
    c4.metric("Entities", len(st.session_state.bedrock_entities))

    st.markdown("---")
    st.subheader("Quick Start")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.info("**Java Mod Builder**\n\nScaffold a Forge / NeoForge project with blocks, items and a ready-to-run `gradlew`. Download the ZIP and build locally.")
    with col_b:
        st.info("**MCBE Addon Creator**\n\nMCreator-like editor for Behavior Packs + Resource Packs. Add items, blocks & simple entities then export a complete addon ZIP.")
    with col_c:
        st.info("**Native / DLL Maker**\n\nGenerate a minimal C++ DLL project template (educational). Useful as a starting point for native modules.")

    st.markdown("---")
    st.subheader("Current Project Snapshot")
    st.json({
        "name": st.session_state.project_name,
        "mod_id": st.session_state.mod_id,
        "author": st.session_state.author,
        "version": st.session_state.version,
        "mc_version": st.session_state.mc_version,
        "namespace": st.session_state.namespace,
        "java_elements": [e["name"] for e in st.session_state.java_elements],
        "bedrock_items": [i["name"] for i in st.session_state.bedrock_items],
        "bedrock_blocks": [b["name"] for b in st.session_state.bedrock_blocks],
        "bedrock_entities": [e["name"] for e in st.session_state.bedrock_entities],
    })

# ===========================================================================
# PAGE: PROJECT SETTINGS
# ===========================================================================
elif page == "⚙️ Project Settings":
    st.title("Project Settings")
    st.markdown("These values are shared across all builders.")

    with st.form("settings_form"):
        col1, col2 = st.columns(2)
        with col1:
            pname = st.text_input("Project / Mod Name", st.session_state.project_name)
            mid = st.text_input("Mod ID / Namespace (lowercase, no spaces)", st.session_state.mod_id)
            author = st.text_input("Author", st.session_state.author)
        with col2:
            ver = st.text_input("Version", st.session_state.version)
            mcver = st.selectbox("Minecraft Version (Java target)", ["1.20.1", "1.20.4", "1.21", "1.21.1"],
                                 index=["1.20.1", "1.20.4", "1.21", "1.21.1"].index(st.session_state.mc_version)
                                 if st.session_state.mc_version in ["1.20.1", "1.20.4", "1.21", "1.21.1"] else 0)
            ns = st.text_input("Bedrock Namespace", st.session_state.namespace)

        if st.form_submit_button("💾 Save Settings"):
            st.session_state.project_name = pname.strip() or "MyAwesomeMod"
            st.session_state.mod_id = safe_id(mid) or "myawesomemod"
            st.session_state.author = author.strip() or "Creator"
            st.session_state.version = ver.strip() or "1.0.0"
            st.session_state.mc_version = mcver
            st.session_state.namespace = safe_id(ns) or "myaddon"
            st.success("Settings saved!")
            st.rerun()

# ===========================================================================
# PAGE: JAVA MOD BUILDER
# ===========================================================================
elif page == "☕ Java Mod Builder":
    st.title("Java Mod Builder")
    st.caption("Generates a complete Forge-style project skeleton. Download the ZIP → open in IntelliJ / VS Code → run `./gradlew build` locally.")

    tab_add, tab_list, tab_export = st.tabs(["➕ Add Element", "📋 Elements", "📦 Export Project"])

    # ---- Add Element ----
    with tab_add:
        etype = st.selectbox("Element Type", ["Item", "Block", "Creative Tab"])
        name = st.text_input("Display Name", "Cool Item")
        eid = st.text_input("Registry Name", safe_id(name) if name else "cool_item")

        extra = {}
        if etype == "Item":
            extra["stack_size"] = st.number_input("Max Stack Size", 1, 64, 64)
            extra["rarity"] = st.selectbox("Rarity", ["COMMON", "UNCOMMON", "RARE", "EPIC"])
        elif etype == "Block":
            extra["hardness"] = st.number_input("Hardness", 0.0, 100.0, 1.5)
            extra["resistance"] = st.number_input("Blast Resistance", 0.0, 100.0, 6.0)
            extra["material"] = st.selectbox("Sound Type", ["STONE", "WOOD", "METAL", "GLASS", "GRASS"])
        elif etype == "Creative Tab":
            extra["icon"] = st.text_input("Icon item (registry name)", "diamond")

        if st.button("➕ Add to Workspace"):
            elem = {
                "id": gen_uuid()[:8],
                "type": etype,
                "name": name,
                "registry": safe_id(eid),
                **extra,
            }
            st.session_state.java_elements.append(elem)
            st.success(f"Added {etype}: {name}")
            st.rerun()

    # ---- List ----
    with tab_list:
        if not st.session_state.java_elements:
            st.info("No elements yet. Add some in the first tab.")
        else:
            for i, e in enumerate(st.session_state.java_elements):
                cols = st.columns([3, 2, 2, 1])
                cols[0].markdown(f"**{e['name']}**")
                cols[1].caption(e["type"])
                cols[2].code(e["registry"])
                if cols[3].button("🗑", key=f"del_java_{i}"):
                    st.session_state.java_elements.pop(i)
                    st.rerun()

    # ---- Export ----
    with tab_export:
        st.markdown("### Generate full mod project")
        loader = st.selectbox("Mod Loader", ["Forge (1.20.1 style)", "NeoForge (template)"])
        group = st.text_input("Maven Group", f"com.{st.session_state.author.lower().replace(' ', '')}")

        if st.button("🚀 Generate & Download ZIP", type="primary"):
            mod_id = st.session_state.mod_id
            pkg = group.replace(".", "/") + "/" + mod_id
            main_class = "".join(w.capitalize() for w in mod_id.split("_")) + "Mod"

            # ---- build.gradle ----
            build_gradle = f'''plugins {{
    id 'eclipse'
    id 'idea'
    id 'maven-publish'
    id 'net.minecraftforge.gradle' version '[6.0,6.2)'
}}

version = '{st.session_state.version}'
group = '{group}'
base {{
    archivesName = '{mod_id}'
}}

java.toolchain.languageVersion = JavaLanguageVersion.of(17)

minecraft {{
    mappings channel: 'official', version: '{st.session_state.mc_version}'

    runs {{
        client {{
            workingDirectory project.file('run')
            property 'forge.logging.markers', 'REGISTRIES'
            property 'forge.logging.console.level', 'debug'
            mods {{
                {mod_id} {{
                    source sourceSets.main
                }}
            }}
        }}
        server {{
            workingDirectory project.file('run')
            property 'forge.logging.markers', 'REGISTRIES'
            property 'forge.logging.console.level', 'debug'
            mods {{
                {mod_id} {{
                    source sourceSets.main
                }}
            }}
        }}
    }}
}}

repositories {{
    mavenCentral()
}}

dependencies {{
    minecraft 'net.minecraftforge:forge:{st.session_state.mc_version}-47.2.0'
}}

tasks.withType(JavaCompile).configureEach {{
    options.encoding = 'UTF-8'
}}
'''

            # ---- mods.toml ----
            mods_toml = f'''modLoader="javafml"
loaderVersion="[47,)"
license="All Rights Reserved"

[[mods]]
modId="{mod_id}"
version="{st.session_state.version}"
displayName="{st.session_state.project_name}"
authors="{st.session_state.author}"
description='''
{st.session_state.project_name} generated by MCBuilder
'''
'''

            # ---- Main mod class ----
            items_reg = ""
            blocks_reg = ""
            for e in st.session_state.java_elements:
                if e["type"] == "Item":
                    items_reg += f'''
    public static final RegistryObject<Item> {e["registry"].upper()} = ITEMS.register("{e["registry"]}",
        () -> new Item(new Item.Properties().stacksTo({e.get("stack_size", 64)})));
'''
                elif e["type"] == "Block":
                    blocks_reg += f'''
    public static final RegistryObject<Block> {e["registry"].upper()} = BLOCKS.register("{e["registry"]}",
        () -> new Block(BlockBehaviour.Properties.of().strength({e.get("hardness", 1.5)}f, {e.get("resistance", 6.0)}f)));
    public static final RegistryObject<Item> {e["registry"].upper()}_ITEM = ITEMS.register("{e["registry"]}",
        () -> new BlockItem({e["registry"].upper()}.get(), new Item.Properties()));
'''

            main_java = f'''package {group}.{mod_id};

import net.minecraft.world.item.Item;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

@Mod("{mod_id}")
public class {main_class} {{
    public static final String MOD_ID = "{mod_id}";

    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, MOD_ID);
    public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(ForgeRegistries.BLOCKS, MOD_ID);
{items_reg}{blocks_reg}
    public {main_class}() {{
        IEventBus bus = FMLJavaModLoadingContext.get().getModEventBus();
        ITEMS.register(bus);
        BLOCKS.register(bus);
    }}
}}
'''

            # ---- gradle wrapper properties (minimal) ----
            gradle_props = '''distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.8-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
'''

            settings_gradle = f'rootProject.name = "{mod_id}"\n'

            # ---- README ----
            readme = f'''# {st.session_state.project_name}

Generated by **MCBuilder** on {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

## Build locally

1. Install **JDK 17**
2. Open this folder in IntelliJ IDEA or VS Code
3. Run:

```bash
./gradlew genEclipseRuns   # or genIntellijRuns
./gradlew build
```

The finished jar appears in `build/libs/`.

## Elements included
'''
            for e in st.session_state.java_elements:
                readme += f"- **{e['type']}**: `{e['registry']}` ({e['name']})\n"

            files = {
                "build.gradle": build_gradle,
                "settings.gradle": settings_gradle,
                "gradle/wrapper/gradle-wrapper.properties": gradle_props,
                f"src/main/java/{pkg}/{main_class}.java": main_java,
                "src/main/resources/META-INF/mods.toml": mods_toml,
                "README.md": readme,
                "gradlew": "#!/bin/sh\n# Placeholder – download real gradlew from a Forge MDK\necho 'Please replace with official Forge gradlew'\n",
            }

            zip_bytes = make_zip(files)
            st.download_button(
                label="⬇️ Download Mod Project ZIP",
                data=zip_bytes,
                file_name=f"{mod_id}-mod-project.zip",
                mime="application/zip",
            )
            st.success("Project generated! Download the ZIP, then run Gradle on your own machine.")
            st.warning("Note: The included `gradlew` is a stub. Copy a real `gradlew` + `gradlew.bat` + `gradle/wrapper/gradle-wrapper.jar` from the official Forge MDK for your Minecraft version.")

# ===========================================================================
# PAGE: MCBE ADDON CREATOR
# ===========================================================================
elif page == "📦 MCBE Addon Creator":
    st.title("MCBE Addon Creator")
    st.caption("MCreator-style editor for Minecraft Bedrock Edition Behavior + Resource Packs.")

    ns = st.session_state.namespace
    tab_item, tab_block, tab_entity, tab_export = st.tabs(
        ["🗡️ Items", "🧱 Blocks", "👾 Entities", "📦 Export Addon"]
    )

    # ---- Items ----
    with tab_item:
        with st.form("add_item"):
            iname = st.text_input("Item Name", "Magic Sword")
            iid = st.text_input("Identifier", f"{ns}:{safe_id(iname)}")
            max_stack = st.number_input("Max Stack", 1, 64, 1)
            category = st.selectbox("Creative Category", ["Equipment", "Items", "Nature", "Construction"])
            if st.form_submit_button("Add Item"):
                st.session_state.bedrock_items.append({
                    "name": iname,
                    "id": iid if ":" in iid else f"{ns}:{safe_id(iid)}",
                    "max_stack": max_stack,
                    "category": category,
                })
                st.success(f"Added item {iname}")
                st.rerun()

        st.markdown("#### Current Items")
        for i, it in enumerate(st.session_state.bedrock_items):
            c1, c2, c3 = st.columns([4, 2, 1])
            c1.write(f"**{it['name']}** — `{it['id']}`")
            c2.caption(f"stack {it['max_stack']} · {it['category']}")
            if c3.button("🗑", key=f"del_item_{i}"):
                st.session_state.bedrock_items.pop(i)
                st.rerun()

    # ---- Blocks ----
    with tab_block:
        with st.form("add_block"):
            bname = st.text_input("Block Name", "Crystal Ore")
            bid = st.text_input("Identifier", f"{ns}:{safe_id(bname)}")
            hardness = st.number_input("Destroy Time", 0.0, 50.0, 3.0)
            if st.form_submit_button("Add Block"):
                st.session_state.bedrock_blocks.append({
                    "name": bname,
                    "id": bid if ":" in bid else f"{ns}:{safe_id(bid)}",
                    "hardness": hardness,
                })
                st.success(f"Added block {bname}")
                st.rerun()

        st.markdown("#### Current Blocks")
        for i, b in enumerate(st.session_state.bedrock_blocks):
            c1, c2, c3 = st.columns([4, 2, 1])
            c1.write(f"**{b['name']}** — `{b['id']}`")
            c2.caption(f"hardness {b['hardness']}")
            if c3.button("🗑", key=f"del_block_{i}"):
                st.session_state.bedrock_blocks.pop(i)
                st.rerun()

    # ---- Entities (very simple) ----
    with tab_entity:
        with st.form("add_entity"):
            ename = st.text_input("Entity Name", "Shadow Wolf")
            eid = st.text_input("Identifier", f"{ns}:{safe_id(ename)}")
            health = st.number_input("Health", 1.0, 100.0, 20.0)
            if st.form_submit_button("Add Entity"):
                st.session_state.bedrock_entities.append({
                    "name": ename,
                    "id": eid if ":" in eid else f"{ns}:{safe_id(eid)}",
                    "health": health,
                })
                st.success(f"Added entity {ename}")
                st.rerun()

        st.markdown("#### Current Entities")
        for i, e in enumerate(st.session_state.bedrock_entities):
            c1, c2, c3 = st.columns([4, 2, 1])
            c1.write(f"**{e['name']}** — `{e['id']}`")
            c2.caption(f"❤ {e['health']}")
            if c3.button("🗑", key=f"del_ent_{i}"):
                st.session_state.bedrock_entities.pop(i)
                st.rerun()

    # ---- Export ----
    with tab_export:
        st.markdown("### Build complete Behavior + Resource Pack")
        pack_name = st.text_input("Pack display name", st.session_state.project_name)
        pack_desc = st.text_area("Description", f"Addon created with MCBuilder by {st.session_state.author}")

        if st.button("🚀 Generate Addon ZIP", type="primary"):
            bp_uuid = gen_uuid()
            bp_mod_uuid = gen_uuid()
            rp_uuid = gen_uuid()
            rp_mod_uuid = gen_uuid()

            # Behavior Pack manifest
            bp_manifest = {
                "format_version": 2,
                "header": {
                    "name": pack_name,
                    "description": pack_desc,
                    "uuid": bp_uuid,
                    "version": [int(x) for x in st.session_state.version.split(".")[:3]] + [0]*(3-len(st.session_state.version.split("."))),
                    "min_engine_version": [1, 20, 0],
                },
                "modules": [{
                    "type": "data",
                    "uuid": bp_mod_uuid,
                    "version": [1, 0, 0],
                }],
                "metadata": {
                    "authors": [st.session_state.author],
                    "generated_with": {"mcbuilder": ["1.0.0"]},
                },
            }

            # Resource Pack manifest
            rp_manifest = {
                "format_version": 2,
                "header": {
                    "name": pack_name + " Resources",
                    "description": pack_desc,
                    "uuid": rp_uuid,
                    "version": [1, 0, 0],
                    "min_engine_version": [1, 20, 0],
                },
                "modules": [{
                    "type": "resources",
                    "uuid": rp_mod_uuid,
                    "version": [1, 0, 0],
                }],
            }

            files = {}
            # manifests
            files["behavior_pack/manifest.json"] = json.dumps(bp_manifest, indent=2)
            files["resource_pack/manifest.json"] = json.dumps(rp_manifest, indent=2)

            # texts
            lang_lines = [f"pack.name={pack_name}", f"pack.description={pack_desc}"]
            for it in st.session_state.bedrock_items:
                short = it["id"].split(":")[-1]
                lang_lines.append(f"item.{it['id']}={it['name']}")
                # item definition
                item_json = {
                    "format_version": "1.20.50",
                    "minecraft:item": {
                        "description": {
                            "identifier": it["id"],
                            "menu_category": {"category": it["category"].lower()},
                        },
                        "components": {
                            "minecraft:max_stack_size": it["max_stack"],
                            "minecraft:icon": {"texture": short},
                        },
                    },
                }
                files[f"behavior_pack/items/{short}.json"] = json.dumps(item_json, indent=2)
                # RP item texture placeholder
                files[f"resource_pack/textures/items/{short}.png.txt"] = "Replace this file with a real 16x16 PNG"

            for b in st.session_state.bedrock_blocks:
                short = b["id"].split(":")[-1]
                lang_lines.append(f"tile.{b['id']}.name={b['name']}")
                block_json = {
                    "format_version": "1.20.50",
                    "minecraft:block": {
                        "description": {"identifier": b["id"]},
                        "components": {
                            "minecraft:destructible_by_mining": {"seconds_to_destroy": b["hardness"]},
                            "minecraft:material_instances": {
                                "*": {"texture": short, "render_method": "opaque"}
                            },
                        },
                    },
                }
                files[f"behavior_pack/blocks/{short}.json"] = json.dumps(block_json, indent=2)
                files[f"resource_pack/textures/blocks/{short}.png.txt"] = "Replace this file with a real 16x16 PNG"

            for e in st.session_state.bedrock_entities:
                short = e["id"].split(":")[-1]
                lang_lines.append(f"entity.{e['id']}.name={e['name']}")
                entity_json = {
                    "format_version": "1.20.50",
                    "minecraft:entity": {
                        "description": {
                            "identifier": e["id"],
                            "is_spawnable": True,
                            "is_summonable": True,
                        },
                        "components": {
                            "minecraft:health": {"value": e["health"], "max": e["health"]},
                            "minecraft:physics": {},
                            "minecraft:collision_box": {"width": 0.6, "height": 1.8},
                        },
                    },
                }
                files[f"behavior_pack/entities/{short}.json"] = json.dumps(entity_json, indent=2)

            files["behavior_pack/texts/en_US.lang"] = "\n".join(lang_lines)
            files["resource_pack/texts/en_US.lang"] = "\n".join(lang_lines)
            files["behavior_pack/texts/languages.json"] = '["en_US"]'
            files["resource_pack/texts/languages.json"] = '["en_US"]'

            # simple terrain texture list so the pack is valid
            terrain = {"texture_data": {}}
            for b in st.session_state.bedrock_blocks:
                short = b["id"].split(":")[-1]
                terrain["texture_data"][short] = {"textures": f"textures/blocks/{short}"}
            files["resource_pack/textures/terrain_texture.json"] = json.dumps(terrain, indent=2)

            item_tex = {"texture_data": {}}
            for it in st.session_state.bedrock_items:
                short = it["id"].split(":")[-1]
                item_tex["texture_data"][short] = {"textures": f"textures/items/{short}"}
            files["resource_pack/textures/item_texture.json"] = json.dumps(item_tex, indent=2)

            files["README.txt"] = textwrap.dedent(f"""
                {pack_name}
                Generated by MCBuilder

                How to install:
                1. Extract this ZIP.
                2. Copy the "behavior_pack" folder into:
                   com.mojang/development_behavior_packs/
                3. Copy the "resource_pack" folder into:
                   com.mojang/development_resource_packs/
                4. Create / open a world → Settings → Add-Ons → activate both packs.
                5. Replace the .png.txt placeholder files with real 16×16 PNG textures.
            """).strip()

            zip_bytes = make_zip(files)
            st.download_button(
                "⬇️ Download Addon ZIP",
                data=zip_bytes,
                file_name=f"{safe_id(pack_name)}-addon.zip",
                mime="application/zip",
            )
            st.success("Addon generated! Extract and place the two packs into your development_* folders.")

# ===========================================================================
# PAGE: NATIVE / DLL MAKER
# ===========================================================================
elif page == "🔌 Native / DLL Maker":
    st.title("Native / DLL Stub Generator")
    st.caption("Educational C++ template for a Windows DLL. Not a complete Minecraft injector — just a clean starting project.")

    st.warning(
        "This generator produces a **basic DLL skeleton** for learning purposes only. "
        "It does **not** contain any Minecraft-specific reverse-engineering, hooks, or cheat code."
    )

    dll_name = st.text_input("DLL Name (no extension)", "MyNativeModule")
    exports = st.text_area(
        "Exported functions (one per line)",
        "HelloFromDll\nGetVersion",
        height=100,
    )
    add_console = st.checkbox("Allocate console on load (for debugging)", True)

    if st.button("🚀 Generate DLL Project ZIP", type="primary"):
        fns = [f.strip() for f in exports.splitlines() if f.strip()]
        export_decls = "\n".join(f'extern "C" __declspec(dllexport) void {f}();' for f in fns)
        export_impls = "\n\n".join(
            f'extern "C" __declspec(dllexport) void {f}() {{\n'
            f'    // TODO: implement {f}\n'
            f'    OutputDebugStringA("{f} called\\n");\n'
            f'}}' for f in fns
        )

        console_code = ""
        if add_console:
            console_code = """
    AllocConsole();
    freopen("CONOUT$", "w", stdout);
    freopen("CONOUT$", "w", stderr);
    std::cout << "[DLL] Loaded successfully\\n";
"""

        dllmain = f'''// {dll_name}.cpp — generated by MCBuilder
#include <windows.h>
#include <iostream>

{export_decls}

{export_impls}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID reserved) {{
    switch (reason) {{
    case DLL_PROCESS_ATTACH:
        DisableThreadLibraryCalls(hModule);
{console_code}
        break;
    case DLL_PROCESS_DETACH:
        break;
    }}
    return TRUE;
}}
'''

        cmakelists = f'''cmake_minimum_required(VERSION 3.15)
project({dll_name} LANGUAGES CXX)

add_library({dll_name} SHARED {dll_name}.cpp)
target_compile_features({dll_name} PRIVATE cxx_std_17)

# On MSVC this produces {dll_name}.dll + .lib
'''

        readme = f'''# {dll_name}

Minimal Windows DLL generated by MCBuilder.

## Build (CMake + MSVC or MinGW)

```bash
mkdir build && cd build
cmake .. -G "Visual Studio 17 2022" -A x64   # or "MinGW Makefiles"
cmake --build . --config Release
```

The resulting `{dll_name}.dll` will be in the build folder.

## Exports
'''
        for f in fns:
            readme += f"- `{f}`\n"

        files = {
            f"{dll_name}.cpp": dllmain,
            "CMakeLists.txt": cmakelists,
            "README.md": readme,
        }
        zip_bytes = make_zip(files)
        st.download_button(
            "⬇️ Download DLL Project ZIP",
            data=zip_bytes,
            file_name=f"{dll_name}-dll-project.zip",
            mime="application/zip",
        )
        st.success("DLL project ready. Build it with CMake + a C++ compiler on your own machine.")

# ===========================================================================
# PAGE: HELP & DEPLOY
# ===========================================================================
elif page == "📖 Help & Deploy":
    st.title("Help & Deploy on Render")
    st.markdown("""
### What this app does
| Section | Output |
|---------|--------|
| **Java Mod Builder** | Full Forge-style project (source + build.gradle). You run `gradlew` **locally**. |
| **MCBE Addon Creator** | Ready-to-install Behavior Pack + Resource Pack ZIP. |
| **Native / DLL Maker** | Clean C++ DLL CMake project (educational). |

### Deploy on Render.com
1. Create a new **Web Service**.
2. Connect a Git repo that contains:
   - `mcbuilder.py` (this file)
   - `requirements.txt` with:
     ```
     streamlit>=1.28.0
     ```
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `streamlit run mcbuilder.py --server.port $PORT --server.address 0.0.0.0`
5. Choose the free instance type.

### Notes
- Real Minecraft mod compilation (Gradle + Minecraft assets) is intentionally **not** performed on the server — it is heavy, requires large downloads, and is better done on your own PC.
- Texture placeholders (`.png.txt`) must be replaced with real 16×16 PNGs before the Bedrock addon looks correct in-game.
- The DLL generator creates a legitimate Windows DLL skeleton only. It does not interact with Minecraft.
""")

    st.markdown("---")
    st.subheader("requirements.txt content")
    st.code("streamlit>=1.28.0\n", language="text")

# Footer
st.markdown("---")
st.caption("MCBuilder · MCreator-inspired toolkit · Generated projects are yours to modify")
