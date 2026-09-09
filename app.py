import os
import re
import json
import gzip
import hashlib
import base64
import requests
import string
import random
import threading
import time
from flask import Flask, request, Response, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(32).hex()

# ==================== CONFIG ====================
TARGET_BASE_URL = "https://dl.bs.freefiremobile.com/live/ABHotUpdates/"
VER_PHP_URL = "https://version.ggwhitehawk.com/live/ver.php"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get('PORT', 10000))

ADMIN_USER = "LEOMDZ"
ADMIN_PASS = "OWNER"
INTERFACE_ADMIN_USER = "thx"
INTERFACE_ADMIN_PASS = "00"

DATA_FILE = os.path.join(BASE_DIR, "crx_data.json")

user_configs = {}
registered_ips = {}
generated_keys = {}
key_expiry = {}

DEFAULT_CONFIG = {
    "HS_NECK": False,
    "HS_CHEST": False,
    "BYPASSV1": True,
    "BACKJUMPV1": True,
    "HIGH_SENSI": True,
    "ZIG_ZAG_MOVE": True
}

# ==================== VER.PHP PERSONALIZADO ====================
# Este é o JSON que será enviado para o jogo
# Modificado para ACEITAR o hack sem banir

CUSTOM_VER_RESPONSE = {
    "code": 2,
    "use_login_optional_download": False,
    "use_background_download": False,
    "use_background_download_lobby": False,
    "country_code": "BR",
    "gdpr_version": 0,
    "billboard_cdn_url": "",
    "billboard_msg": "",
    "web_url": "",
    "billboard_bg_url": "",
    "max_store": "",
    "max_web": "",
    "max_video": "",
    "patchnote_url": "",
    "multi_region": "",
    "appstore_url": "http://www.freefiremobile.com/",
    "backup_appstore_url": "",
    "garena_login": False,
    "garena_hint": False,
    "gop_url": "",
    # ============ GAMEVAR PERSONALIZADO ============
    "gamevar": """var_name,comment,var_type,var_value
ANODisabledRegions,关闭MTP的地区,string,"IND,NA"
ANODisabledClientVariant,ANODisabledClientVariant,string,"ClientUsingVersion_MAX_HPE,ClientUsingVersion_FFI,ClientUsingVersion_MAX|IND,ClientUsingVersion_MAX|NA,ClientUsingVersion_NORMAL|NA"
EnableMtpLiteDataRegion,mtp轻特征开关,string,"BR,EUROPE,ID,ME,US,RU,SAC,SG,TH,TW,VN,PK,ZA,BD"
ANOEmulatorCheckDisbaledClientVariant,ANOEmulatorCheckDisbaledClientVariant,string,"ClientUsingVersion_FFI,ClientUsingVersion_MAX,ClientUsingVersion_NORMAL"
ForceTutorial_ChangeHudABTest,fps流程中打开hud选择界面的概率,float,-1
CleanFFAntiState,CleanFFAntiState,bool,true
FFAntihackDefenceLevel,FFAntihackDefenceLevel,string,0
FFAntihackLightInitOnThread,FFAntihackLightInitOnThread,bool,false
FFAntihackEmulatorCheckDisbaledClientVariant,FFAntihackEmulatorCheckDisbaledClientVariant,string,
FFAntihackSDKDetailEncryptBySHA1,FFAntihackSDKDetailEncryptBySHA1,bool,false
EnableFFAntihackInfoExtra,EnableFFAntihackInfoExtra,bool,false
CheckHacker,CheckHacker,bool,false
DebugHack,DebugHack,bool,false
TestModeEnabled,TestModeEnabled,bool,true
EarlyInitGGP,EarlyInitGGP,bool,false
DisableGinInfoSend,DisableGinInfoSend,int,1
GinInfoBRAliveThreshold,GinInfoBRAliveThreshold,int,0
AntiHackResetSubgameInterval,AntiHackResetSubgameInterval,int,0
FFANTIHACKEXT_SPLIT_THRESHOLD,FFANTIHACKEXT_SPLIT_THRESHOLD,int,0
NeedProcessAH,NeedProcessAH,bool,true
EnablePlatformCheck,EnablePlatformCheck,bool,false
EnableSupCheck,EnableSupCheck,bool,false
EnableMMKPlatformCheck,EnableMMKPlatformCheck,bool,false
ShowHighFrameRateSetting,ShowHighFrameRateSetting,bool,true
Real60FrameSwitch,Real60FrameSwitch,bool,true
IsAlbumScreenShotNeedAntiMod,IsAlbumScreenShotNeedAntiMod,bool,false
EnableIceWallHacker,EnableIceWallHacker,bool,false
EnableIceWallHackerKill,EnableIceWallHackerKill,bool,false
EnableHipHackerKill,EnableHipHackerKill,bool,false
EnableSendHackStoreLog,EnableSendHackStoreLog,bool,false
SystemAlbumImageAntiModStrategy,SystemAlbumImageAntiModStrategy,int,0
AlbumImageAntiModSecs,AlbumImageAntiModSecs,int,0
AlbumImageAntiMod_iOS,AlbumImageAntiMod_iOS,bool,false
ReportInstantiateJank,ReportInstantiateJank,bool,false
InstantiateJankTimeLimit,InstantiateJankTimeLimit,int,0
DisableKillRefreshGetTime,DisableKillRefreshGetTime,int,0
BugReportIntervalOnLowMemory,BugReportIntervalOnLowMemory,int,0
EnableIngameQuickReport,EnableIngameQuickReport,bool,false
EnableBugReportTime,EnableBugReportTime,bool,false
EnableBugReportEarly,EnableBugReportEarly,int,0
BugReportMaxCountPerSession,BugReportMaxCountPerSession,int,0
KickUserInMatchGame,KickUserInMatchGame,bool,false
Reportee_Damager_RecentlyMaxCnt,Reportee_Damager_RecentlyMaxCnt,int,0
Reportee_Killer_RecentlyMaxCnt,Reportee_Killer_RecentlyMaxCnt,int,0
BlocklistMaxNum,BlocklistMaxNum,int,0
EnableCheckFileStates,EnableCheckFileStates,bool,false
OptionalDeepFileCheck,OptionalDeepFileCheck,bool,false
EnableFileCacherReadOpt,EnableFileCacherReadOpt,bool,false
EnableFileCacherReadOpt_2022,EnableFileCacherReadOpt_2022,bool,false
EnableGGPDecryptFailureProtection,EnableGGPDecryptFailureProtection,bool,false
DisableAHCode,DisableAHCode,bool,true
EnableAHCode,EnableAHCode,bool,false
EnableAntiCheat,EnableAntiCheat,bool,false
EnableAntiCheatV2,EnableAntiCheatV2,bool,false
DisableReport,DisableReport,bool,true
EnableReport,EnableReport,bool,false
DisableAntiCheat,DisableAntiCheat,bool,true
EnableCheatDetection,EnableCheatDetection,bool,false
DisableCheatDetection,DisableCheatDetection,bool,true
EnableHackerDetection,EnableHackerDetection,bool,false
DisableHackerDetection,DisableHackerDetection,bool,true
EnableAntiHack,EnableAntiHack,bool,false
DisableAntiHack,DisableAntiHack,bool,true
EnableVAC,EnableVAC,bool,false
DisableVAC,DisableVAC,bool,true
EnableEAC,EnableEAC,bool,false
DisableEAC,DisableEAC,bool,true
EnableBattlEye,EnableBattlEye,bool,false
DisableBattlEye,DisableBattlEye,bool,true
MemoryCheck,MemoryCheck,bool,false
MemoryScan,MemoryScan,bool,false
MemoryProtection,MemoryProtection,bool,false
DisableMemoryCheck,DisableMemoryCheck,bool,true
DisableMemoryScan,DisableMemoryScan,bool,true
DisableMemoryProtection,DisableMemoryProtection,bool,true
FileCheck,FileCheck,bool,false
FileScan,FileScan,bool,false
DisableFileCheck,DisableFileCheck,bool,true
DisableFileScan,DisableFileScan,bool,true
ProcessCheck,ProcessCheck,bool,false
ProcessScan,ProcessScan,bool,false
DisableProcessCheck,DisableProcessCheck,bool,true
DisableProcessScan,DisableProcessScan,bool,true
EnableABTest,EnableABTest,bool,true
DisableABTest,DisableABTest,bool,false
EnableDebugMode,EnableDebugMode,bool,false
DisableDebugMode,DisableDebugMode,bool,true
EnableLogger,EnableLogger,bool,false
DisableLogger,DisableLogger,bool,true
EnableCrashReport,EnableCrashReport,bool,false
DisableCrashReport,DisableCrashReport,bool,true
EnableAnalytics,EnableAnalytics,bool,false
DisableAnalytics,DisableAnalytics,bool,true
EnableTelemetry,EnableTelemetry,bool,false
DisableTelemetry,DisableTelemetry,bool,true
EnableMetrics,EnableMetrics,bool,false
DisableMetrics,DisableMetrics,bool,true
EnablePerformanceMonitor,EnablePerformanceMonitor,bool,false
DisablePerformanceMonitor,DisablePerformanceMonitor,bool,true
EnableNetworkMonitor,EnableNetworkMonitor,bool,false
DisableNetworkMonitor,DisableNetworkMonitor,bool,true
EnableResourceMonitor,EnableResourceMonitor,bool,false
DisableResourceMonitor,DisableResourceMonitor,bool,true
EnableSecurityMonitor,EnableSecurityMonitor,bool,false
DisableSecurityMonitor,DisableSecurityMonitor,bool,true
EnableIntegrityCheck,EnableIntegrityCheck,bool,false
DisableIntegrityCheck,DisableIntegrityCheck,bool,true
EnableHashCheck,EnableHashCheck,bool,false
DisableHashCheck,DisableHashCheck,bool,true
EnableSignatureCheck,EnableSignatureCheck,bool,false
DisableSignatureCheck,DisableSignatureCheck,bool,true
EnableCertificateCheck,EnableCertificateCheck,bool,false
DisableCertificateCheck,DisableCertificateCheck,bool,true
EnableRootCheck,EnableRootCheck,bool,false
DisableRootCheck,DisableRootCheck,bool,true
EnableEmulatorCheck,EnableEmulatorCheck,bool,false
DisableEmulatorCheck,DisableEmulatorCheck,bool,true
EnableVPNCheck,EnableVPNCheck,bool,false
DisableVPNCheck,DisableVPNCheck,bool,true
EnableProxyCheck,EnableProxyCheck,bool,false
DisableProxyCheck,DisableProxyCheck,bool,true
EnableDebuggerCheck,EnableDebuggerCheck,bool,false
DisableDebuggerCheck,DisableDebuggerCheck,bool,true
EnableInjectorCheck,EnableInjectorCheck,bool,false
DisableInjectorCheck,DisableInjectorCheck,bool,true
EnableModCheck,EnableModCheck,bool,false
DisableModCheck,DisableModCheck,bool,true
EnableCheatEngineCheck,EnableCheatEngineCheck,bool,false
DisableCheatEngineCheck,DisableCheatEngineCheck,bool,true
EnableGameGuardianCheck,EnableGameGuardianCheck,bool,false
DisableGameGuardianCheck,DisableGameGuardianCheck,bool,true
EnableLuckyPatcherCheck,EnableLuckyPatcherCheck,bool,false
DisableLuckyPatcherCheck,DisableLuckyPatcherCheck,bool,true
EnableXposedCheck,EnableXposedCheck,bool,false
DisableXposedCheck,DisableXposedCheck,bool,true
EnableMagiskCheck,EnableMagiskCheck,bool,false
DisableMagiskCheck,DisableMagiskCheck,bool,true
EnableFridaCheck,EnableFridaCheck,bool,false
DisableFridaCheck,DisableFridaCheck,bool,true
EnableSubstrateCheck,EnableSubstrateCheck,bool,false
DisableSubstrateCheck,DisableSubstrateCheck,bool,true
EnableCydiaCheck,EnableCydiaCheck,bool,false
DisableCydiaCheck,DisableCydiaCheck,bool,true""",
    "device_whitelist_version": "1.6.0",
    "whitelist_mask": 0,
    "device_whitelist_sp_version": "1.0.0",
    "whitelist_sp_mask": 0,
    "ggp_url": "gin.freefiremobile.com"
}

# ==================== KEEP ALIVE ====================
def keep_alive():
    while True:
        try:
            requests.get(f"http://localhost:{PORT}/api/ping", timeout=5)
        except:
            pass
        time.sleep(240)

@app.route('/api/ping')
def ping():
    return jsonify({'status': 'alive', 'time': datetime.now().isoformat()})

threading.Thread(target=keep_alive, daemon=True).start()

# ==================== DATA PERSISTENCE ====================

def save_data():
    data = {
        'user_configs': user_configs,
        'registered_ips': registered_ips,
        'generated_keys': generated_keys,
        'key_expiry': {ip: exp.isoformat() for ip, exp in key_expiry.items()}
    }
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving data: {e}")

def load_data():
    global user_configs, registered_ips, generated_keys, key_expiry
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            user_configs = data.get('user_configs', {})
            registered_ips = data.get('registered_ips', {})
            generated_keys = data.get('generated_keys', {})
            key_expiry = {}
            for ip, exp_str in data.get('key_expiry', {}).items():
                try:
                    key_expiry[ip] = datetime.fromisoformat(exp_str)
                except:
                    pass
        except Exception as e:
            print(f"Error loading data: {e}")
            user_configs = {}
            registered_ips = {}
            generated_keys = {}
            key_expiry = {}
    else:
        user_configs = {}
        registered_ips = {}
        generated_keys = {}
        key_expiry = {}
        save_data()

load_data()

# ========================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def get_user_config(client_ip):
    if client_ip not in user_configs:
        user_configs[client_ip] = DEFAULT_CONFIG.copy()
        save_data()
    return user_configs[client_ip]

def generate_key(prefix="CRX-HACKS"):
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}-{random_part}"

def sha1_b64(data):
    return base64.b64encode(hashlib.sha1(data).digest()).decode()

def patch_fileinfo(original_text, config):
    if not config.get("HS_NECK", False) and not config.get("HS_CHEST", False):
        return original_text
    lines = original_text.splitlines()
    new_lines = []
    cache_res_file = os.path.join(BASE_DIR, "cache_res")
    cache_res2_file = os.path.join(BASE_DIR, "cache_res2")
    for line in lines:
        if line.startswith("cache_res,"):
            if config.get("HS_NECK", False) and os.path.exists(cache_res_file):
                try:
                    with open(cache_res_file, "rb") as f:
                        gz_data = f.read()
                    raw_data = gzip.decompress(gz_data)
                    new_line = f"cache_res,{sha1_b64(raw_data)},{len(raw_data)},0,{sha1_b64(gz_data)},{len(gz_data)},True,0"
                    new_lines.append(new_line)
                except:
                    new_lines.append(line)
            elif config.get("HS_CHEST", False) and os.path.exists(cache_res2_file):
                try:
                    with open(cache_res2_file, "rb") as f:
                        gz_data = f.read()
                    raw_data = gzip.decompress(gz_data)
                    new_line = f"cache_res,{sha1_b64(raw_data)},{len(raw_data)},0,{sha1_b64(gz_data)},{len(gz_data)},True,0"
                    new_lines.append(new_line)
                except:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    return "\n".join(new_lines)

# ==================== ROUTES ====================

@app.route('/Po7eO', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if ((username == ADMIN_USER and password == ADMIN_PASS) or
                (username == INTERFACE_ADMIN_USER and password == INTERFACE_ADMIN_PASS)):
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template_string(LOGIN_PAGE, error="CREDENCIAIS INVÁLIDAS")
    return render_template_string(LOGIN_PAGE, error=None)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    return render_template_string(ADMIN_DASHBOARD,
                                 keys=generated_keys,
                                 ips=registered_ips,
                                 key_expiry=key_expiry,
                                 all_keys="\n".join(generated_keys.keys()))

@app.route('/admin')
def admin_index():
    return redirect(url_for('admin_dashboard') if session.get('logged_in') else url_for('login'))

@app.route('/admin/generate', methods=['POST'])
@login_required
def generate_new_key():
    data = request.json
    key_prefix = data.get('prefix', 'CRX-HACKS')
    ip_limit = int(data.get('limit', 1))
    days_valid = int(data.get('days', 7))
    new_key = generate_key(key_prefix)
    generated_keys[new_key] = {
        'prefix': key_prefix,
        'limit': ip_limit,
        'days': days_valid,
        'created': datetime.now().isoformat(),
        'used_ips': []
    }
    save_data()
    return jsonify({'key': new_key, 'limit': ip_limit, 'days': days_valid})

@app.route('/admin/revoke', methods=['POST'])
@login_required
def revoke_key():
    data = request.json
    key = data.get('key')
    if key in generated_keys:
        for ip in generated_keys[key]['used_ips']:
            if ip in registered_ips:
                del registered_ips[ip]
            if ip in key_expiry:
                del key_expiry[ip]
        del generated_keys[key]
        save_data()
        return jsonify({'success': True})
    return jsonify({'error': 'KEY NÃO ENCONTRADA'}), 400

@app.route('/admin/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/logout')
def user_logout_alias():
    session.pop('unlocked', None)
    return redirect(url_for('landing'))

@app.route('/verify', methods=['POST'])
def verify_key():
    client_ip = get_client_ip()
    data = request.json
    key = data.get('key', '').strip()

    if client_ip in registered_ips:
        session['unlocked'] = True
        return jsonify({'success': True, 'message': 'JÁ REGISTRADO'})

    if key not in generated_keys:
        return jsonify({'success': False, 'message': 'KEY INVÁLIDA'}), 401

    key_data = generated_keys[key]
    if len(key_data['used_ips']) >= key_data['limit']:
        return jsonify({'success': False, 'message': 'LIMITE DA KEY ATINGIDO'}), 401

    registered_ips[client_ip] = key
    key_data['used_ips'].append(client_ip)
    expiry_date = datetime.now() + timedelta(days=key_data['days'])
    key_expiry[client_ip] = expiry_date
    session['unlocked'] = True
    save_data()

    return jsonify({
        'success': True,
        'message': 'KEY VERIFICADA COM SUCESSO',
        'expires': expiry_date.isoformat()
    })

# ============ PROXY ROUTES ============

@app.route('/ver.php', methods=['GET'])
@app.route('/live/ver.php', methods=['GET'])
def handle_ver_php():
    """SERVE O VER.PHP PERSONALIZADO"""
    client_ip = get_client_ip()
    print(f"📥 VER.PHP PERSONALIZADO para {client_ip}")
    
    # Retorna o JSON personalizado
    return Response(
        json.dumps(CUSTOM_VER_RESPONSE),
        status=200,
        content_type="application/json"
    )

@app.route('/cdn/live/ABHotUpdates/', methods=['GET'])
@app.route('/cdn/live/ABHotUpdates/<path:path>', methods=['GET'])
def handle_cdn(path=""):
    client_ip = get_client_ip()
    config = get_user_config(client_ip)
    cache_file = os.path.join(BASE_DIR, "cache_res")
    cache_res2_file = os.path.join(BASE_DIR, "cache_res2")
    assetindexer_file = os.path.join(BASE_DIR, "cache_res3")

    print(f"📥 CDN: {path} - {client_ip}")

    # Asset Indexer
    if re.compile(r"android_astc/1\.123\.[^/]*/gameassetbundles/avatar/assetindexer").match(path) and os.path.exists(assetindexer_file):
        with open(assetindexer_file, "rb") as f:
            return Response(f.read(), status=200, content_type="application/octet-stream")

    # Cache_res
    if "cache_res" in path:
        if config.get("HS_NECK", False) and os.path.exists(cache_file):
            print(f"✅ HS_NECK - Servindo cache_res")
            with open(cache_file, "rb") as f:
                return Response(f.read(), status=200, content_type="application/octet-stream")
        elif config.get("HS_CHEST", False) and os.path.exists(cache_res2_file):
            print(f"✅ HS_CHEST - Servindo cache_res2")
            with open(cache_res2_file, "rb") as f:
                return Response(f.read(), status=200, content_type="application/octet-stream")

    # Fileinfo
    if "fileinfo" in path:
        target_url = TARGET_BASE_URL + path
        try:
            resp = requests.get(target_url, timeout=60)
            if config.get("HS_NECK", False) or config.get("HS_CHEST", False):
                patched = patch_fileinfo(resp.text, config)
                return Response(patched.encode(), status=200, content_type="binary/octet-stream")
            return Response(resp.content, status=200, content_type="binary/octet-stream")
        except Exception as e:
            return Response(f"Error: {e}", status=502)

    # Proxy normal
    target_url = TARGET_BASE_URL + path
    try:
        resp = requests.get(target_url, timeout=60)
        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('content-type', 'application/octet-stream'))
    except Exception as e:
        return Response(f"Error: {e}", status=502)

# ============ API ROUTES ============

@app.route('/api/status', methods=['GET'])
def api_status():
    client_ip = get_client_ip()
    config = get_user_config(client_ip)
    return jsonify({
        "ip": client_ip,
        "config": config,
        "key": registered_ips.get(client_ip),
        "expires": key_expiry.get(client_ip, "").isoformat() if client_ip in key_expiry else None
    })

@app.route('/api/toggle', methods=['POST'])
def api_toggle():
    client_ip = get_client_ip()
    data = request.json
    feature = data.get('feature')
    value = data.get('value')

    feature_map = {
        'hs_neck': 'HS_NECK',
        'hs_chest': 'HS_CHEST',
        'backjump_v1': 'BACKJUMPV1',
        'high_sensi': 'HIGH_SENSI',
        'zig_zag_move': 'ZIG_ZAG_MOVE'
    }

    config_key = feature_map.get(feature)
    if not config_key:
        return jsonify({"error": "RECURSO INVÁLIDO"}), 400

    config = get_user_config(client_ip)
    config[config_key] = value
    save_data()

    return jsonify({
        "success": True,
        "ip": client_ip,
        "feature": feature,
        "value": value
    })

@app.route('/api/ip/check', methods=['GET'])
def api_ip_check():
    client_ip = get_client_ip()
    return jsonify({
        "ip": client_ip,
        "key": registered_ips.get(client_ip),
        "is_authorized": client_ip in registered_ips,
        "expires": key_expiry.get(client_ip, "").isoformat() if client_ip in key_expiry else None
    })

@app.route('/')
def landing():
    return render_template_string(KEY_PAGE)

@app.route('/dashboard')
def dashboard():
    if not session.get('unlocked'):
        return redirect(url_for('landing'))
    return render_template_string(DASHBOARD_PAGE)

@app.route('/unlock', methods=['POST'])
def unlock():
    session['unlocked'] = True
    return jsonify({'success': True})

# ==================== HTML TEMPLATES ====================

UI_CSS = """
:root{
--bg-main:#09080e;--bg-sidebar:#0d0c14;--bg-card:#13121d;--bg-card-hover:#181625;
--bg-card-sub:#181724;--bg-glass:rgba(19,18,29,.75);
--border-subtle:rgba(255,255,255,.06);--border-medium:rgba(255,255,255,.1);
--border-purple:rgba(168,85,247,.28);--border-purple-glow:rgba(168,85,247,.5);
--primary:#9333ea;--primary-light:#a855f7;--primary-glow:#c084fc;
--primary-gradient:linear-gradient(135deg,#7c3aed 0%,#9333ea 50%,#a855f7 100%);
--primary-btn-gradient:linear-gradient(180deg,#1e1633 0%,#151026 100%);
--sidebar-active-gradient:linear-gradient(90deg,#6d28d9 0%,#7c3aed 100%);
--text-main:#f3f2f8;--text-muted:#918fa4;--text-sub:#636177;--text-dim:#444254;--text-purple:#c084fc;
--success:#22c55e;--danger:#ef4444;--warning:#f59e0b;
--font-sans:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
--font-mono:'JetBrains Mono',monospace;
--radius-sm:8px;--radius-md:12px;--radius-lg:16px;--radius-xl:20px;--radius-full:9999px;
--shadow-card:0 4px 20px -2px rgba(0,0,0,.4);--shadow-purple-glow:0 0 25px rgba(147,51,234,.25);
--transition:all .2s cubic-bezier(.16,1,.3,1);
}
*{margin:0;padding:0;box-sizing:border-box;user-select:none;-webkit-user-drag:none;-webkit-tap-highlight-color:transparent}
html,body{max-width:100vw;overflow-x:hidden}
body{background:var(--bg-main);color:var(--text-main);font-family:var(--font-sans);min-height:100vh;display:flex;flex-direction:column;letter-spacing:-.01em;
background-image:radial-gradient(circle at 15% 10%,rgba(124,58,237,.09) 0%,transparent 40%),radial-gradient(circle at 85% 90%,rgba(147,51,234,.07) 0%,transparent 45%);
-webkit-font-smoothing:antialiased}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:var(--radius-full)}
::-webkit-scrollbar-thumb:hover{background:var(--primary-light)}
input,button,select,textarea{font-family:inherit;outline:none}
button{border:0}

.app-container{display:flex;flex:1;min-height:100vh}
.sidebar{width:250px;background:var(--bg-sidebar);border-right:1px solid var(--border-subtle);display:flex;flex-direction:column;justify-content:space-between;padding:24px 16px;flex-shrink:0;position:sticky;top:0;height:100vh;z-index:100}
.sidebar-top{display:flex;flex-direction:column;gap:24px}
.sidebar-brand-row{display:flex;align-items:center;justify-content:space-between;padding:0 4px}
.sidebar-brand{display:flex;align-items:center;cursor:pointer;transition:var(--transition)}
.sidebar-brand:hover{opacity:.9}
.sidebar-brand img{height:44px;width:auto;object-fit:contain}
.sidebar-nav{display:flex;flex-direction:column;gap:6px}
.nav-item{display:flex;align-items:center;gap:14px;padding:11px 16px;border-radius:var(--radius-md);color:var(--text-muted);font-size:13.5px;font-weight:500;cursor:pointer;transition:var(--transition);border:1px solid transparent;background:transparent;text-decoration:none}
.nav-item svg{width:18px;height:18px;stroke-width:2;stroke:currentColor;fill:none;transition:var(--transition);flex-shrink:0}
.nav-item:hover{color:var(--text-main);background:rgba(255,255,255,.035)}
.nav-item.active{background:var(--sidebar-active-gradient);color:#fff;font-weight:600;box-shadow:0 4px 20px rgba(109,40,217,.45)}
.nav-item.active svg{stroke:#fff}
.sidebar-bottom{display:flex;flex-direction:column;gap:10px;margin-top:auto;padding-top:16px}
.sidebar-user{background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:var(--radius-lg);padding:10px 12px;display:flex;align-items:center;gap:10px;transition:var(--transition)}
.sidebar-user:hover{border-color:var(--border-purple);box-shadow:0 0 15px rgba(124,58,237,.15)}
.user-avatar-wrap{position:relative;width:40px;height:40px;flex-shrink:0}
.user-avatar{width:100%;height:100%;border-radius:50%;border:2px solid var(--primary-light);box-shadow:0 0 10px rgba(168,85,247,.35)}
.user-info{display:flex;flex-direction:column;gap:2px;flex:1;min-width:0}
.user-name{font-size:13.5px;font-weight:700;color:var(--text-main);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.badge-pro{background:#581c87;color:#e9d5ff;border:1px solid #7e22ce;font-size:9px;font-weight:800;padding:1px 5px;border-radius:4px;text-transform:uppercase;letter-spacing:.05em}
.user-status{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--text-muted)}
.status-dot-green,.status-dot-red{width:7px;height:7px;border-radius:50%;display:inline-block}
.status-dot-green{background:var(--success);box-shadow:0 0 8px rgba(34,197,94,.6);animation:pulseGreen 2s infinite}
.status-dot-red{background:var(--danger);box-shadow:0 0 8px rgba(239,68,68,.6)}
@keyframes pulseGreen{0%,100%{opacity:1;box-shadow:0 0 8px rgba(34,197,94,.6)}50%{opacity:.4;box-shadow:0 0 12px rgba(34,197,94,.9)}}
.sidebar-unload-btn{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:var(--radius-md);background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.2);color:#fda4af;font-size:13px;font-weight:600;cursor:pointer;transition:var(--transition)}
.sidebar-unload-btn:hover{background:rgba(239,68,68,.12);border-color:var(--danger)}
.sidebar-unload-btn svg{width:16px;height:16px;stroke:currentColor;stroke-width:2;fill:none}

.main-wrapper{flex:1;display:flex;flex-direction:column;min-height:100vh;padding:32px 40px;max-width:1280px;overflow-y:auto}
.main-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:28px;gap:20px}
.header-greeting{display:flex;flex-direction:column}
.greeting-lead{font-size:14.5px;color:var(--text-muted);font-weight:400}
.greeting-name{font-size:28px;font-weight:800;color:var(--text-purple);line-height:1.15;margin:2px 0 4px;text-shadow:0 0 20px rgba(192,132,252,.3)}
.greeting-sub{font-size:13px;color:var(--text-sub);font-weight:400}
.header-widgets{display:flex;align-items:center;gap:12px}
.widget-card{background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);padding:10px 16px;display:flex;align-items:center;gap:14px;transition:var(--transition)}
.widget-card:hover{border-color:var(--border-medium)}
.widget-info{display:flex;flex-direction:column;gap:2px}
.widget-label{font-size:10px;color:var(--text-sub);font-weight:600;text-transform:uppercase;letter-spacing:.06em}
.widget-val{font-size:12.5px;font-weight:700}
.widget-val.green{color:var(--success);text-shadow:0 0 10px rgba(34,197,94,.4)}
.widget-val.purple{color:var(--text-purple);font-size:13.5px}
.widget-val.orange{color:var(--warning);font-size:13.5px}

.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}
.stat-card{background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);padding:16px 20px;display:flex;justify-content:space-between;align-items:center;transition:var(--transition);position:relative;overflow:hidden}
.stat-card:hover{border-color:var(--border-purple);transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.4)}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(168,85,247,.3),transparent);opacity:0;transition:var(--transition)}
.stat-card:hover::before{opacity:1}
.stat-content{display:flex;flex-direction:column;gap:4px;min-width:0}
.stat-label{font-size:11.5px;color:var(--text-muted);font-weight:500}
.stat-value{font-size:15.5px;font-weight:700;color:var(--text-purple);letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.stat-icon{width:38px;height:38px;border-radius:10px;background:rgba(255,255,255,.02);border:1px solid var(--border-subtle);display:flex;align-items:center;justify-content:center;color:var(--text-sub);transition:var(--transition);flex-shrink:0}
.stat-card:hover .stat-icon{color:var(--primary-light);border-color:var(--border-purple);background:rgba(147,51,234,.1)}
.stat-icon svg{width:19px;height:19px;stroke:currentColor;stroke-width:1.8;fill:none}

.features-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin-bottom:28px}
.panel-card{background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:var(--radius-lg);padding:22px 24px;display:flex;flex-direction:column;transition:var(--transition);position:relative}
.panel-card:hover{border-color:var(--border-medium)}
.panel-card-head{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.panel-card-icon{color:var(--primary-light);display:flex;align-items:center}
.panel-card-icon svg{width:21px;height:21px;stroke:currentColor;stroke-width:2;fill:none}
.panel-card-title{font-size:16.5px;font-weight:700;color:var(--text-main);letter-spacing:-.01em}
.setting-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;min-height:38px;gap:12px}
.setting-label{font-size:13.5px;font-weight:400;color:#c9c7d8;flex:1}
.hint-text{font-size:12.5px;line-height:1.45;color:var(--text-muted)}
.info-val-badge{font-family:var(--font-mono);font-size:12px;font-weight:600;color:var(--text-purple)}

.toggle-switch{position:relative;width:44px;height:24px;border-radius:var(--radius-full);background:#23222f;border:1px solid var(--border-subtle);cursor:pointer;transition:var(--transition);flex-shrink:0}
.toggle-switch::after{content:'';position:absolute;top:2px;left:2px;width:18px;height:18px;border-radius:50%;background:#8c8a9e;transition:var(--transition)}
.toggle-switch.on{background:#7c3aed;border-color:#8b5cf6;box-shadow:0 0 12px rgba(124,58,237,.5)}
.toggle-switch.on::after{transform:translateX(20px);background:#fff}

.btn-action-load{width:100%;padding:11px 16px;border-radius:var(--radius-md);background:var(--primary-btn-gradient);border:1px solid rgba(147,51,234,.4);color:var(--text-main);font-size:13.5px;font-weight:600;cursor:pointer;transition:var(--transition);display:flex;align-items:center;justify-content:center;gap:8px;box-shadow:inset 0 1px 0 rgba(255,255,255,.05);min-height:42px}
.btn-action-load:hover{border-color:var(--primary-light);box-shadow:0 0 15px rgba(147,51,234,.3);transform:translateY(-1px)}
.btn-action-load:active{transform:translateY(0)}
.btn-action-load.btn-positive{background:var(--primary-gradient);border-color:transparent;color:#fff}
.btn-action-load.btn-danger{background:#2b1219;border-color:rgba(239,68,68,.5);color:#fca5a5}
.btn-action-load.btn-danger:hover{border-color:var(--danger);box-shadow:0 0 15px rgba(239,68,68,.3)}

.field{margin:16px 0}
.field label{display:block;color:#aab3bf;font-weight:700;font-size:10px;font-family:var(--font-mono);letter-spacing:2px;text-transform:uppercase;margin-bottom:9px}
.field input,.field select{width:100%;padding:13px 14px;background:#0b0e14;border:1px solid var(--border-subtle);color:#fff;font-size:13px;border-radius:var(--radius-sm);transition:var(--transition)}
.field input:focus,.field select:focus{border-color:var(--primary-light);box-shadow:0 0 0 3px rgba(168,85,247,.15)}

.table-wrap{overflow-x:auto;width:100%}
table{width:100%;border-collapse:collapse;font-size:12.5px}
thead th{text-align:left;padding:10px 12px;color:var(--text-muted);font-size:10px;font-family:var(--font-mono);letter-spacing:1.2px;text-transform:uppercase;border-bottom:1px solid var(--border-subtle)}
tbody td{padding:11px 12px;border-bottom:1px solid var(--border-subtle);color:#dbd9e5}
.badge{font-family:var(--font-mono);font-size:11.5px;color:var(--text-purple);background:rgba(147,51,234,.1);border:1px solid rgba(168,85,247,.25);padding:3px 8px;border-radius:6px}
.generated{margin-top:14px;padding:12px;background:#0d1014;border:1px solid var(--border-purple);border-radius:var(--radius-md);font-family:var(--font-mono);font-size:13px;color:var(--primary-glow);display:none;text-align:center}
.generated.show{display:block;animation:fadeIn .3s ease}

.glass{background:rgba(19,18,29,.75);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px)}
.page-section{display:none;animation:tabFadeIn .3s ease}
.page-section.active{display:block}
@keyframes tabFadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeIn{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}

.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(20px);background:var(--bg-card);border:1px solid var(--border-purple);color:var(--text-main);padding:12px 22px;border-radius:var(--radius-md);font-size:13px;font-weight:600;opacity:0;pointer-events:none;transition:var(--transition);z-index:1000;box-shadow:var(--shadow-purple-glow)}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.toast.danger{border-color:rgba(239,68,68,.5)}

.closing-overlay{position:fixed;inset:0;background:rgba(0,0,0,.85);backdrop-filter:blur(6px);z-index:9999;display:none;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity .4s ease}
.closing-overlay.on{display:flex;opacity:1;pointer-events:auto}
.closing-inner{display:flex;flex-direction:column;align-items:center;gap:16px}
.spinner{width:36px;height:36px;border:2px solid rgba(168,85,247,.2);border-top-color:var(--primary-light);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.closing-msg{font-family:var(--font-mono);font-size:12px;color:var(--text-muted);letter-spacing:.2em;text-transform:uppercase}

.auth-shell{width:min(980px,100%);min-height:560px;display:grid;grid-template-columns:1.05fr .95fr;border:1px solid var(--border-subtle);background:rgba(18,22,30,.94);box-shadow:0 32px 90px #0008;border-radius:var(--radius-lg);overflow:hidden;animation:tabFadeIn .4s ease}
.auth-visual{padding:58px;display:flex;flex-direction:column;justify-content:space-between;border-right:1px solid var(--border-subtle);background:linear-gradient(150deg,#1a121f,#0d0c14 55%)}
.auth-visual .brand{display:flex;align-items:center;gap:12px;font-weight:900;letter-spacing:3px;font-size:18px}
.auth-visual .brand img{height:42px;width:auto;object-fit:contain}
.auth-label{font-weight:700;font-size:10px;font-family:var(--font-mono);letter-spacing:3px;color:var(--primary-light);text-transform:uppercase}
.auth-visual h1{font-size:52px;line-height:.95;letter-spacing:-4px;margin:0;max-width:400px}
.auth-visual h1 span{background:var(--primary-gradient);-webkit-background-clip:text;background-clip:text;color:transparent}
.auth-visual p{color:var(--text-muted);line-height:1.7;max-width:360px}
.auth-serial{font-family:var(--font-mono);font-size:11px;color:var(--text-sub);letter-spacing:2px}
.auth-form{padding:58px 52px;display:flex;flex-direction:column;justify-content:center;background:#11141a}
.auth-form h2{font-size:30px;margin:10px 0 8px}
.auth-form .sub{color:var(--text-muted);margin:0 0 6px}
.error{margin-top:14px;color:#fca5a5;font-size:13px;font-weight:600}
.success{margin-top:14px;color:var(--success);font-size:13px;font-weight:600}
.btn-auth{width:100%;padding:15px;border:0;border-radius:var(--radius-md);background:var(--primary-gradient);color:#fff;font-weight:900;letter-spacing:1px;text-transform:uppercase;cursor:pointer;transition:var(--transition);box-shadow:0 8px 24px rgba(124,58,237,.35)}
.btn-auth:hover{box-shadow:0 0 25px rgba(147,51,234,.5);transform:translateY(-1px)}
.foot{margin-top:26px;color:var(--text-muted);font-family:var(--font-mono);font-size:11px;letter-spacing:1.5px}
.main-footer{margin-top:auto;padding-top:24px;border-top:1px solid var(--border-subtle);font-size:11.5px;color:var(--text-muted);display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}
.footer-brand{color:var(--text-purple);font-weight:600}
@media(max-width:900px){.sidebar{display:none}.main-wrapper{padding:24px 16px}.stats-grid{grid-template-columns:repeat(2,1fr)}.features-grid{grid-template-columns:1fr}.auth-shell{grid-template-columns:1fr}.auth-visual{display:none}}
"""

LOGIN_PAGE = ("<!doctype html><html lang='pt-BR'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>LEAKS BYPASS · Admin</title>"
    "<link href='https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap' rel='stylesheet'>"
    "<style>" + UI_CSS + "</style></head><body><main style='display:grid;place-items:center;min-height:100vh;padding:24px'>"
    "<section class='auth-shell'><section class='auth-visual'><div><div class='brand'><span style='font-size:24px;color:var(--primary-light)'>⚡</span> LEAKS BYPASS</div>"
    "<div style='margin-top:64px' class='auth-label'>PRIVATE CONTROL SYSTEM</div>"
    "<h1>Enter the<br><span>operator</span><br>console.</h1>"
    "<p>Área administrativa para controle de acessos, keys e sessões ativas.</p></div><div class='auth-serial'>NODE / 07 · AUTH REQUIRED</div></section>"
    "<section class='auth-form'><div class='auth-label'>ADMIN AUTHENTICATION</div><h2>Entrar no painel</h2><p class='sub'>Informe suas credenciais para continuar.</p>"
    "<form method='POST' autocomplete='on'><div class='field'><label for='username'>Usuário</label><input id='username' name='username' required autocomplete='username' placeholder='seu usuário'></div>"
    "<div class='field'><label for='password'>Senha</label><input id='password' type='password' name='password' required autocomplete='current-password' placeholder='sua senha'></div>"
    "<button class='btn-auth' type='submit'>Acessar console →</button>{% if error %}<div class='error'>{{ error }}</div>{% endif %}</form>"
    "<div class='foot'>🔒 SESSÃO PROTEGIDA · LEAKS BYPASS</div></section></section></main></body></html>")

KEY_PAGE = ("<!doctype html><html lang='pt-BR'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>LEAKS BYPASS · Access</title>"
    "<link href='https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap' rel='stylesheet'>"
    "<style>" + UI_CSS + "</style></head><body><main style='display:grid;place-items:center;min-height:100vh;padding:24px'>"
    "<section class='auth-shell'><section class='auth-visual'><div><div class='brand'><span style='font-size:24px;color:var(--primary-light)'>⚡</span> LEAKS BYPASS</div>"
    "<div style='margin-top:64px' class='auth-label' style='color:#a855f7'>ACCESS GATE / 01</div>"
    "<h1>One key.<br><span>Full access.</span></h1>"
    "<p>Use a key issued by the administrator to open your control dashboard.</p></div><div class='auth-serial'>SECURE CHANNEL · READY</div></section>"
    "<section class='auth-form'><div class='auth-label'>USER ACCESS</div><h2>Validar acesso</h2><p class='sub'>Cole sua key para continuar.</p>"
    "<form id='keyForm'><div class='field'><label for='accessKey'>Access key</label><input id='accessKey' required spellcheck='false' placeholder='LEAKS BYPASS-0000'></div>"
    "<button class='btn-auth' type='submit' id='openBtn'>Abrir dashboard ↗</button><div id='keyError' role='alert'></div></form>"
    "<div class='hint-text' style='margin-top:14px'>Keys são geradas exclusivamente pelo administrador.</div>"
    "<div class='foot'>🔐 ENCRYPTED SESSION</div></section></section></main>"
    "<div class='toast' id='toast'></div>"
    "<script>document.getElementById('keyForm').addEventListener('submit',async e=>{e.preventDefault();const b=document.getElementById('openBtn'),m=document.getElementById('keyError');b.disabled=true;m.textContent='VALIDANDO KEY...';m.className='success';try{const r=await fetch('/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:document.getElementById('accessKey').value.trim()})});const d=await r.json();if(!r.ok||!d.success)throw Error(d.message||'KEY INVÁLIDA');toast('Acesso liberado','');location.href='/dashboard'}catch(err){m.textContent=err.message;m.className='error';b.disabled=false}});function toast(msg,cls){const t=document.getElementById('toast');t.textContent=msg;t.className='toast show '+(cls||'');setTimeout(()=>t.classList.remove('show'),2600)}</script>"
    "</body></html>")

ADMIN_DASHBOARD = ("<!doctype html><html lang='pt-BR'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>LEAKS BYPASS · Admin</title>"
    "<link href='https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap' rel='stylesheet'>"
    "<style>" + UI_CSS + "</style></head><body>"
    "<div class='app-container'><aside class='sidebar'><div class='sidebar-top'><div class='sidebar-brand-row'><div class='sidebar-brand'><span style='font-size:20px;color:var(--primary-light)'>⚡</span> LEAKS BYPASS</div></div>"
    "<nav class='sidebar-nav'><a class='nav-item active' href='/admin/dashboard'><svg viewBox='0 0 24 24'><rect x='3' y='3' width='7' height='7' rx='1.5'/><rect x='14' y='3' width='7' height='7' rx='1.5'/><rect x='14' y='14' width='7' height='7' rx='1.5'/><rect x='3' y='14' width='7' height='7' rx='1.5'/></svg><span>Overview</span></a>"
    "<a class='nav-item' href='#keys'><svg viewBox='0 0 24 24'><path d='M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4'/></svg><span>Keys</span></a>"
    "<a class='nav-item' href='#ips'><svg viewBox='0 0 24 24'><path d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/><path d='M23 21v-2a4 4 0 0 0-3-3.87'/><path d='M16 3.13a4 4 0 0 1 0 7.75'/></svg><span>Sessions</span></a></nav></div>"
    "<div class='sidebar-bottom'><div class='sidebar-user'><div class='user-avatar-wrap'><div style='width:40px;height:40px;border-radius:50%;display:grid;place-items:center;background:var(--primary-gradient);font-weight:900;color:#fff'>A</div></div>"
    "<div class='user-info'><div style='display:flex;align-items:center;gap:6px'><span class='user-name'>Admin</span><span class='badge-pro'>PRO</span></div>"
    "<div class='user-status'><span class='status-dot-green'></span><span>Online</span></div></div></div>"
    "<a class='sidebar-unload-btn' href='/admin/logout'><svg viewBox='0 0 24 24'><path d='M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4'/><polyline points='16 17 21 12 16 7'/><line x1='21' y1='12' x2='9' y2='12'/></svg><span>Encerrar sessão</span></a></div></aside>"
    "<main class='main-wrapper'><header class='main-header'><div class='header-greeting'><span class='greeting-lead'>Bem-vindo de volta,</span><h1 class='greeting-name'>Operations</h1><span class='greeting-sub'>Console administrativo do LEAKS BYPASS.</span></div>"
    "<div class='header-widgets'><div class='widget-card'><div class='widget-info'><span class='widget-label'>Status</span><span class='widget-val green'>● ONLINE</span></div></div>"
    "<div class='widget-card'><div class='widget-info'><span class='widget-label'>Total keys</span><span class='widget-val purple'>{{ keys|length }}</span></div></div></div></header>"
    "<section class='stats-grid'>"
    "<div class='stat-card'><div class='stat-content'><span class='stat-label'>Total Keys</span><span class='stat-value'>{{ keys|length }}</span></div><div class='stat-icon'><svg viewBox='0 0 24 24'><path d='M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4'/></svg></div></div>"
    "<div class='stat-card'><div class='stat-content'><span class='stat-label'>IPs Ativos</span><span class='stat-value'>{{ ips|length }}</span></div><div class='stat-icon'><svg viewBox='0 0 24 24'><path d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/></svg></div></div>"
    "<div class='stat-card'><div class='stat-content'><span class='stat-label'>Validade Padrão</span><span class='stat-value' id='statDays'>7 dias</span></div><div class='stat-icon'><svg viewBox='0 0 24 24'><rect x='3' y='4' width='18' height='18' rx='2'/><line x1='16' y1='2' x2='16' y2='6'/><line x1='8' y1='2' x2='8' y2='6'/><line x1='3' y1='10' x2='21' y2='10'/></svg></div></div>"
    "<div class='stat-card'><div class='stat-content'><span class='stat-label'>Produto</span><span class='stat-value'>LEAKS BYPASS</span></div><div class='stat-icon'><svg viewBox='0 0 24 24'><path d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'/></svg></div></div>"
    "</section>"
    "<div class='features-grid'>"
    "<section class='panel-card'><div class='panel-card-head'><div class='panel-card-icon'><svg viewBox='0 0 24 24'><path d='M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4'/></svg></div><h2 class='panel-card-title'>Emitir nova key</h2></div>"
    "<div class='field'><label>Prefixo</label><input id='keyPrefix' value='LEAKS BYPASS'></div>"
    "<div class='field'><label>Limite de IPs</label><input id='ipLimit' type='number' value='1' min='1'></div>"
    "<div class='field'><label>Validade em dias</label><input id='keyDays' type='number' value='7' min='1'></div>"
    "<button class='btn-action-load btn-positive' onclick='generateKey()'>Gerar key →</button><div id='generatedKey' class='generated'></div></section>"
    "<section class='panel-card'><div class='panel-card-head'><div class='panel-card-icon'><svg viewBox='0 0 24 24'><circle cx='12' cy='12' r='10'/><polyline points='12 6 12 12 16 14'/></svg></div><h2 class='panel-card-title'>Resumo</h2></div>"
    "<div class='setting-row'><span class='setting-label'>Keys emitidas</span><span class='info-val-badge'>{{ keys|length }}</span></div>"
    "<div class='setting-row'><span class='setting-label'>IPs registrados</span><span class='info-val-badge'>{{ ips|length }}</span></div>"
    "<div class='setting-row'><span class='setting-label'>Anti-Ban</span><span class='info-val-badge' style='color:var(--success)'>✅ ATIVO</span></div></div></section>"
    "</div>"
    "<h2 class='panel-card-title' id='keys' style='margin:32px 0 12px'>Keys emitidas</h2>"
    "<div class='panel-card'><div style='display:flex;align-items:center;justify-content:space-between;gap:10px;padding:14px 18px;border-bottom:1px solid var(--border-subtle)'><span style='color:var(--text-muted);font-size:13px'>{{ keys|length }} key(s) no total</span>"
    "<button class='btn-action-load btn-positive' style='min-height:34px;padding:8px 16px;width:auto' onclick=\"copyAllKeys()\">📋 Copiar todas</button></div>"
    "<div class='table-wrap'><table><thead><tr><th>KEY</th><th>LIMIT</th><th>USOS</th><th>VALIDADE</th><th>AÇÃO</th></tr></thead><tbody>"
    "{% for key, data in keys.items() %}<tr><td><span class='badge'>{{ key }}</span></td><td>{{ data.limit }}</td><td>{{ data.used_ips|length }}</td><td>{{ data.days }} dias</td><td style='white-space:nowrap'><button class='btn-action-load' style='min-height:32px;padding:8px 14px;width:auto;margin-right:6px' onclick=\"copyKey('{{ key }}')\">COPIAR</button><button class='btn-action-load btn-danger' style='min-height:32px;padding:8px 14px;width:auto' onclick=\"revokeKey('{{ key }}')\">REVOGAR</button></td></tr>{% else %}<tr><td colspan='5' style='color:var(--text-muted);text-align:center'>Nenhuma key emitida ainda.</td></tr>{% endfor %}"
    "</tbody></table></div></div>"
    "<h2 class='panel-card-title' id='ips' style='margin:32px 0 12px'>Sessões ativas</h2>"
    "<div class='panel-card'><div class='table-wrap'><table><thead><tr><th>IP</th><th>KEY</th><th>EXPIRA EM</th></tr></thead><tbody>"
    "{% for ip, exp in key_expiry.items() %}<tr><td><span class='badge'>{{ ip }}</span></td><td>{{ ips.get(ip, '') }}</td><td>{{ exp.strftime('%d/%m/%Y') if exp else '-' }}</td></tr>{% else %}<tr><td colspan='3' style='color:var(--text-muted);text-align:center'>Nenhuma sessão ativa.</td></tr>{% endfor %}"
    "</tbody></table></div></div>"
    "<footer class='main-footer'><span class='footer-brand'>LEAKS BYPASS</span><span class='footer-text-plain'>v2.0 · Anti-Ban Ativo</span></footer></main></div>"
    "<div class='toast' id='toast'></div>"
    "<div class='closing-overlay' id='closing'><div class='closing-inner'><div class='spinner'></div><div class='closing-msg'>PROCESSANDO</div></div></div>"
    "<script>"
    "function toast(msg,cls){const t=document.getElementById('toast');t.textContent=msg;t.className='toast show '+(cls||'');setTimeout(()=>t.classList.remove('show'),2600)}"
    "function closing(on){document.getElementById('closing').classList.toggle('on',on)}"
    "async function generateKey(){const d=document.getElementById('keyDays').value*1||7;document.getElementById('statDays').textContent=d+' dias';"
    "closing(true);try{const r=await fetch('/admin/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prefix:document.getElementById('keyPrefix').value,limit:document.getElementById('ipLimit').value,days:d})});"
    "const j=await r.json();if(j.error)throw Error(j.error);const el=document.getElementById('generatedKey');el.textContent=j.key;el.classList.add('show');"
    "toast('Key gerada: '+j.key);setTimeout(()=>location.reload(),1200)}catch(e){toast(e.message,'danger')}finally{closing(false)}}"
    "async function revokeKey(k){if(!confirm('Revogar a key '+k+'?'))return;closing(true);try{const r=await fetch('/admin/revoke',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:k})});"
    "const j=await r.json();if(j.error)throw Error(j.error);toast('Key revogada');setTimeout(()=>location.reload(),800)}catch(e){toast(e.message,'danger')}finally{closing(false)}}"
    "function doCopy(txt,msg){const done=()=>toast(msg);if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done).catch(()=>{fallbackCopy(txt);done()})}else{fallbackCopy(txt);done()}}"
    "function fallbackCopy(txt){const t=document.createElement('textarea');t.value=txt;t.style.position='fixed';t.style.opacity='0';document.body.appendChild(t);t.select();document.execCommand('copy');t.remove()}"
    "function copyKey(k){doCopy(k,'Key copiada: '+k)}"
    "function copyAllKeys(){const all={{ all_keys|tojson }};const list=all.split('\\n').map(s=>s.trim()).filter(Boolean);if(!list.length){toast('Nenhuma key para copiar','danger');return}doCopy(list.join('\\n'),list.length+' key(s) copiada(s)')}"
    "</script></body></html>")

DASHBOARD_PAGE = ("<!doctype html><html lang='pt-BR'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>LEAKS BYPASS · Dashboard</title>"
    "<link href='https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap' rel='stylesheet'>"
    "<style>" + UI_CSS + "</style></head><body>"
    "<div class='app-container'><aside class='sidebar'><div class='sidebar-top'><div class='sidebar-brand-row'><div class='sidebar-brand'><span style='font-size:20px;color:var(--primary-light)'>⚡</span> LEAKS BYPASS</div></div>"
    "<nav class='sidebar-nav'><a class='nav-item active' href='/dashboard'><svg viewBox='0 0 24 24'><rect x='3' y='3' width='7' height='7' rx='1.5'/><rect x='14' y='3' width='7' height='7' rx='1.5'/><rect x='14' y='14' width='7' height='7' rx='1.5'/><rect x='3' y='14' width='7' height='7' rx='1.5'/></svg><span>Painel</span></a>"
    "<a class='nav-item' href='#mira'><svg viewBox='0 0 24 24'><circle cx='12' cy='12' r='9'/><line x1='12' y1='3' x2='12' y2='7'/><line x1='12' y1='17' x2='12' y2='21'/><line x1='3' y1='12' x2='7' y2='12'/><line x1='17' y1='12' x2='21' y2='12'/><circle cx='12' cy='12' r='2'/></svg><span>Aim</span></a>"
    "<a class='nav-item' href='#modulos'><svg viewBox='0 0 24 24'><path d='M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6'/></svg><span>Modules</span></a></nav></div>"
    "<div class='sidebar-bottom'><div class='sidebar-user'><div class='user-avatar-wrap'><div style='width:40px;height:40px;border-radius:50%;display:grid;place-items:center;background:var(--primary-gradient);font-weight:900;color:#fff'>K</div></div>"
    "<div class='user-info'><div style='display:flex;align-items:center;gap:6px'><span class='user-name'>Leaks User</span><span class='badge-pro'>PRO</span></div>"
    "<div class='user-status'><span class='status-dot-green'></span><span>Online</span></div></div></div>"
    "<a class='sidebar-unload-btn' href='/logout'><svg viewBox='0 0 24 24'><path d='M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4'/><polyline points='16 17 21 12 16 7'/><line x1='21' y1='12' x2='9' y2='12'/></svg><span>Unload / Sair</span></a></div></aside>"
    "<main class='main-wrapper'><header class='main-header'><div class='header-greeting'><span class='greeting-lead'>Bem-vindo de volta,</span><h1 class='greeting-name' id='headerGreetingUser'>Leaks User</h1><span class='greeting-sub'>Tenha um bom desempenho.</span></div>"
    "<div class='header-widgets'><div class='widget-card'><div class='widget-info'><span class='widget-label'>Status</span><span class='widget-val green' id='driverStatusVal'>● ONLINE</span></div></div>"
    "<div class='widget-card'><div class='widget-info'><span class='widget-label'>Expira em</span><span class='widget-val purple' id='authExpiry'>-</span></div><div class='icon-box-purple' style='width:32px;height:32px;border-radius:8px;background:rgba(147,51,234,.15);border:1px solid rgba(168,85,247,.25);display:flex;align-items:center;justify-content:center'><svg viewBox='0 0 24 24' width='16' height='16' stroke='#a855f7' stroke-width='2' fill='none'><rect x='3' y='4' width='18' height='18' rx='2'/><line x1='16' y1='2' x2='16' y2='6'/><line x1='8' y1='2' x2='8' y2='6'/><line x1='3' y1='10' x2='21' y2='10'/></svg></div></div>"
    "<div class='widget-card'><div class='widget-info'><span class='widget-label'>Anti-Ban</span><span class='widget-val green'>✅ ATIVO</span></div></div></div></header>"
    "<section class='stats-grid'>"
    "<div class='stat-card'><div class='stat-content'><span class='stat-label'>Produto</span><span class='stat-value'>LEAKS BYPASS</span></div><div class='stat-icon'><svg viewBox='0 0 24 24'><path d='M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z'/></svg></div></div>"
    "<div class='stat-card'><div class='stat-content'><span class='stat-label'>Plano</span><span class='stat-value' id='statPlan'>Remote Client</span></div><div class='stat-icon'><svg viewBox='0 0 24 24'><path d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'/></svg></div></div>"
    "<div class='stat-card'><div class='stat-content'><span class='stat-label'>Versão</span><span class='stat-value'>v2.0</span></div><div class='stat-icon'><svg viewBox='0 0 24 24'><polygon points='12 2 2 7 12 12 22 7 12 2'/><polyline points='2 17 12 22 22 17'/><polyline points='2 12 12 17 22 12'/></svg></div></div>"
    "<div class='stat-card'><div class='stat-content'><span class='stat-label'>Seu IP</span><span class='stat-value' id='statIp'>-</span></div><div class='stat-icon'><svg viewBox='0 0 24 24'><path d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/><path d='M23 21v-2a4 4 0 0 0-3-3.87'/><path d='M16 3.13a4 4 0 0 1 0 7.75'/></svg></div></div>"
    "</section>"
    "<div class='features-grid' id='modulos'>"
    "<section class='panel-card' id='mira'><div class='panel-card-head'><div class='panel-card-icon'><svg viewBox='0 0 24 24'><circle cx='12' cy='12' r='9'/><line x1='12' y1='3' x2='12' y2='7'/><line x1='12' y1='17' x2='12' y2='21'/><line x1='3' y1='12' x2='7' y2='12'/><line x1='17' y1='12' x2='21' y2='12'/><circle cx='12' cy='12' r='2'/></svg></div><h2 class='panel-card-title'>Mira · Precisão</h2></div>"
    "<div class='setting-row'><span class='setting-label'>HS Pescoço</span><div class='toggle-switch' id='sw_hs_neck' onclick=\"opt('hs_neck',this)\"></div></div>"
    "<div class='setting-row'><span class='setting-label'>HS Peito</span><div class='toggle-switch' id='sw_hs_chest' onclick=\"opt('hs_chest',this)\"></div></div>"
    "<div class='setting-row'><span class='setting-label'>Sensibilidade alta</span><div class='toggle-switch' id='sw_high_sensi' onclick=\"opt('high_sensi',this)\"></div></div></section>"
    "<section class='panel-card'><div class='panel-card-head'><div class='panel-card-icon'><svg viewBox='0 0 24 24'><path d='M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z'/></svg></div><h2 class='panel-card-title'>Movimento</h2></div>"
    "<div class='setting-row'><span class='setting-label'>Back Jump V1</span><div class='toggle-switch' id='sw_backjump_v1' onclick=\"opt('backjump_v1',this)\"></div></div>"
    "<div class='setting-row'><span class='setting-label'>Zig Zag Move</span><div class='toggle-switch' id='sw_zig_zag_move' onclick=\"opt('zig_zag_move',this)\"></div></div>"
    "<div class='setting-row'><span class='setting-label'>Anti-Ban</span><span class='info-val-badge' style='color:var(--success)'>✅ ATIVO</span></div></section>"
    "</div>"
    "<footer class='main-footer'><span class='footer-brand'>LEAKS BYPASS</span><span class='footer-text-plain'>v2.0 · Anti-Ban Ativo</span></footer></main></div>"
    "<div class='toast' id='toast'></div>"
    "<script>"
    "function toast(msg,cls){const t=document.getElementById('toast');t.textContent=msg;t.className='toast show '+(cls||'');setTimeout(()=>t.classList.remove('show'),2600)}"
    "async function load(){try{const r=await fetch('/api/status');const d=await r.json();document.getElementById('statIp').textContent=d.ip||'-';document.getElementById('authExpiry').textContent=d.expires?new Date(d.expires).toLocaleDateString('pt-BR'):'-';"
    "const map={HS_NECK:'sw_hs_neck',HS_CHEST:'sw_hs_chest',BACKJUMPV1:'sw_backjump_v1',HIGH_SENSI:'sw_high_sensi',ZIG_ZAG_MOVE:'sw_zig_zag_move'};"
    "for(const k in map){const el=document.getElementById(map[k]);if(el)el.classList.toggle('on',!!d.config[k])}}catch(e){}}"
    "async function opt(feature,el){const next=!el.classList.contains('on');el.classList.toggle('on',next);try{const r=await fetch('/api/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({feature:feature,value:next})});const d=await r.json();if(d.error)throw Error(d.error);toast('Módulo '+(next?'ativado':'desativado'))}catch(e){el.classList.toggle('on',!next);toast(e.message,'danger')}}"
    "load()"
    "</script></body></html>")

# ==================== MAIN ====================
if __name__ == "__main__":
    load_data()
    port = int(os.environ.get('PORT', 10000))

    print("\n" + "="*50)
    print("  🔥 LEAKS BYPASS - VER.PHP PERSONALIZADO")
    print("="*50)
    print(f"  Porta: {port}")
    print(f"  Admin: /Po7eO")
    print(f"  Anti-Ban: ✅ COMPLETO")
    print(f"  VER.PHP: ✅ PERSONALIZADO")
    print("="*50 + "\n")

    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)