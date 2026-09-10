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

# ==================== ANTI-BAN COMPLETO ====================
ANTI_BAN_OVERRIDES = {
    "CleanFFAntiState": {"var_type": "bool", "var_value": "true"},
    "FFAntihackDefenceLevel": {"var_type": "string", "var_value": "0"},
    "FFAntihackLightInitOnThread": {"var_type": "bool", "var_value": "false"},
    "FFAntihackEmulatorCheckDisbaledClientVariant": {"var_type": "string", "var_value": ""},
    "FFAntihackSDKDetailEncryptBySHA1": {"var_type": "bool", "var_value": "false"},
    "EnableFFAntihackInfoExtra": {"var_type": "bool", "var_value": "false"},
    "CheckHacker": {"var_type": "bool", "var_value": "false"},
    "DebugHack": {"var_type": "bool", "var_value": "false"},
    "TestModeEnabled": {"var_type": "bool", "var_value": "true"},
    "EarlyInitGGP": {"var_type": "bool", "var_value": "false"},
    "DisableGinInfoSend": {"var_type": "int", "var_value": "1"},
    "GinInfoBRAliveThreshold": {"var_type": "int", "var_value": "0"},
    "AntiHackResetSubgameInterval": {"var_type": "int", "var_value": "0"},
    "FFANTIHACKEXT_SPLIT_THRESHOLD": {"var_type": "int", "var_value": "0"},
    "NeedProcessAH": {"var_type": "bool", "var_value": "true"},
    "EnablePlatformCheck": {"var_type": "bool", "var_value": "false"},
    "EnableSupCheck": {"var_type": "bool", "var_value": "false"},
    "EnableMMKPlatformCheck": {"var_type": "bool", "var_value": "false"},
    "ShowHighFrameRateSetting": {"var_type": "bool", "var_value": "true"},
    "Real60FrameSwitch": {"var_type": "bool", "var_value": "true"},
    "IsAlbumScreenShotNeedAntiMod": {"var_type": "bool", "var_value": "false"},
    "EnableIceWallHacker": {"var_type": "bool", "var_value": "false"},
    "EnableIceWallHackerKill": {"var_type": "bool", "var_value": "false"},
    "EnableHipHackerKill": {"var_type": "bool", "var_value": "false"},
    "EnableSendHackStoreLog": {"var_type": "bool", "var_value": "false"},
    "SystemAlbumImageAntiModStrategy": {"var_type": "int", "var_value": "0"},
    "AlbumImageAntiModSecs": {"var_type": "int", "var_value": "0"},
    "AlbumImageAntiMod_iOS": {"var_type": "bool", "var_value": "false"},
    "ReportInstantiateJank": {"var_type": "bool", "var_value": "false"},
    "InstantiateJankTimeLimit": {"var_type": "int", "var_value": "0"},
    "DisableKillRefreshGetTime": {"var_type": "int", "var_value": "0"},
    "BugReportIntervalOnLowMemory": {"var_type": "int", "var_value": "0"},
    "EnableIngameQuickReport": {"var_type": "bool", "var_value": "false"},
    "EnableBugReportTime": {"var_type": "bool", "var_value": "false"},
    "EnableBugReportEarly": {"var_type": "int", "var_value": "0"},
    "BugReportMaxCountPerSession": {"var_type": "int", "var_value": "0"},
    "KickUserInMatchGame": {"var_type": "bool", "var_value": "false"},
    "Reportee_Damager_RecentlyMaxCnt": {"var_type": "int", "var_value": "0"},
    "Reportee_Killer_RecentlyMaxCnt": {"var_type": "int", "var_value": "0"},
    "BlocklistMaxNum": {"var_type": "int", "var_value": "0"},
    "EnableCheckFileStates": {"var_type": "bool", "var_value": "false"},
    "OptionalDeepFileCheck": {"var_type": "bool", "var_value": "false"},
    "EnableFileCacherReadOpt": {"var_type": "bool", "var_value": "false"},
    "EnableFileCacherReadOpt_2022": {"var_type": "bool", "var_value": "false"},
    "EnableGGPDecryptFailureProtection": {"var_type": "bool", "var_value": "false"},
    # Extra anti-ban
    "DisableAHCode": {"var_type": "bool", "var_value": "true"},
    "EnableAHCode": {"var_type": "bool", "var_value": "false"},
    "EnableAntiCheat": {"var_type": "bool", "var_value": "false"},
    "EnableAntiCheatV2": {"var_type": "bool", "var_value": "false"},
    "DisableReport": {"var_type": "bool", "var_value": "true"},
    "EnableReport": {"var_type": "bool", "var_value": "false"},
    "DisableAntiCheat": {"var_type": "bool", "var_value": "true"},
    "EnableCheatDetection": {"var_type": "bool", "var_value": "false"},
    "DisableCheatDetection": {"var_type": "bool", "var_value": "true"},
    "EnableHackerDetection": {"var_type": "bool", "var_value": "false"},
    "DisableHackerDetection": {"var_type": "bool", "var_value": "true"},
    "EnableAntiHack": {"var_type": "bool", "var_value": "false"},
    "DisableAntiHack": {"var_type": "bool", "var_value": "true"},
    "EnableVAC": {"var_type": "bool", "var_value": "false"},
    "DisableVAC": {"var_type": "bool", "var_value": "true"},
    "EnableEAC": {"var_type": "bool", "var_value": "false"},
    "DisableEAC": {"var_type": "bool", "var_value": "true"},
    "EnableBattlEye": {"var_type": "bool", "var_value": "false"},
    "DisableBattlEye": {"var_type": "bool", "var_value": "true"},
    "MemoryCheck": {"var_type": "bool", "var_value": "false"},
    "MemoryScan": {"var_type": "bool", "var_value": "false"},
    "MemoryProtection": {"var_type": "bool", "var_value": "false"},
    "DisableMemoryCheck": {"var_type": "bool", "var_value": "true"},
    "DisableMemoryScan": {"var_type": "bool", "var_value": "true"},
    "DisableMemoryProtection": {"var_type": "bool", "var_value": "true"},
    "FileCheck": {"var_type": "bool", "var_value": "false"},
    "FileScan": {"var_type": "bool", "var_value": "false"},
    "DisableFileCheck": {"var_type": "bool", "var_value": "true"},
    "DisableFileScan": {"var_type": "bool", "var_value": "true"},
    "ProcessCheck": {"var_type": "bool", "var_value": "false"},
    "ProcessScan": {"var_type": "bool", "var_value": "false"},
    "DisableProcessCheck": {"var_type": "bool", "var_value": "true"},
    "DisableProcessScan": {"var_type": "bool", "var_value": "true"},
}

BACKJUMPV1_OVERRIDES = {
    "EnableAccelerationOnFalling": {"var_type": "bool", "var_value": "false"},
    "CanJumpFallingRunFast": {"var_type": "bool", "var_value": "false"},
    "CanCreepRunFast": {"var_type": "bool", "var_value": "false"},
    "CanCrouchingRunFast": {"var_type": "bool", "var_value": "false"},
    "StropFallingResetSpeed": {"var_type": "bool", "var_value": "true"}
}

HIGH_SENSI_OVERRIDES = {
    "SensitivityMaxSetting": {"var_type": "float", "var_value": "9.0"},
    "Sensitivity1PMaxSetting": {"var_type": "float", "var_value": "9.0"},
    "X1ScopeMaxSetting": {"var_type": "float", "var_value": "9.0"},
    "X2ScopeMaxSetting": {"var_type": "float", "var_value": "9.0"},
    "X4ScopeMaxSetting": {"var_type": "float", "var_value": "9.0"},
    "X8ScopeMaxSetting": {"var_type": "float", "var_value": "9.0"},
    "FreeLookMaxSetting": {"var_type": "float", "var_value": "9.0"}
}

ZIG_ZAG_MOVE_OVERRIDES = {
    "FreeMoveAngularSpeed": {"var_type": "float", "var_value": "9999.0"},
    "FreeMoveAngularSpeedStand": {"var_type": "float", "var_value": "9999.0"},
    "FreeMoveAngularSpeedCrouch": {"var_type": "float", "var_value": "9999.0"},
    "FreeMoveAngularSpeedCreep": {"var_type": "float", "var_value": "9999.0"},
    "ResetRotationSpeed": {"var_type": "float", "var_value": "9999.0"},
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

def get_overrides_for_ip(client_ip):
    config = get_user_config(client_ip)
    overrides = {}
    # SEMPRE APLICA ANTI-BAN
    overrides.update(ANTI_BAN_OVERRIDES)
    if config.get("BACKJUMPV1", False):
        overrides.update(BACKJUMPV1_OVERRIDES)
    if config.get("HIGH_SENSI", False):
        overrides.update(HIGH_SENSI_OVERRIDES)
    if config.get("ZIG_ZAG_MOVE", False):
        overrides.update(ZIG_ZAG_MOVE_OVERRIDES)
    return overrides

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

def modify_ver_response(response_text, client_ip):
    """Modifica o ver.php original para injetar anti-ban e mudar CDN"""
    try:
        data = json.loads(response_text)
        
        # Muda as URLs do CDN para o nosso servidor
        cdn_url = f"https://{request.host}/cdn/live/ABHotUpdates/"
        data["cdn_url"] = cdn_url
        data["backup_cdn_url"] = cdn_url
        data["abhotupdate_cdn_url"] = cdn_url
        
        # Adiciona as variáveis de anti-ban no gamevar
        overrides = get_overrides_for_ip(client_ip)
        if overrides:
            gamevar = data.get("gamevar", "")
            for var_name, override in overrides.items():
                gamevar += f"\n{var_name},{var_name},{override['var_type']},{override['var_value']},,"
            data["gamevar"] = gamevar
        
        print(f"✅ VER.PHP modificado para {client_ip}")
        return json.dumps(data)
    except Exception as e:
        print(f"❌ Erro modify_ver_response: {e}")
        return response_text

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
    """Baixa o ver.php original e injeta anti-ban"""
    client_ip = get_client_ip()
    params = dict(request.args)
    headers = {k: v for k, v in request.headers.items() 
               if k.lower() not in ("host", "content-length", "connection", "accept-encoding")}
    
    try:
        # Baixa o ver.php original com todos os parâmetros
        response = requests.get(VER_PHP_URL, params=params, headers=headers, timeout=60)
        original_text = response.text
        
        # Modifica a resposta
        modified = modify_ver_response(original_text, client_ip)
        
        print(f"✅ VER.PHP modificado para {client_ip}")
        return Response(modified, status=200, content_type="application/json")
    except Exception as e:
        print(f"❌ Erro ao baixar ver.php: {e}")
        return Response(f"Error: {e}", status=502)

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
# (Mantenha os mesmos templates UI_CSS, LOGIN_PAGE, KEY_PAGE, ADMIN_DASHBOARD, DASHBOARD_PAGE)
# Para economizar espaço, não vou reescrevê-los aqui, mas você deve mantê-los.
# Eles são os mesmos do código anterior.

# ==================== MAIN ====================
if __name__ == "__main__":
    load_data()
    port = int(os.environ.get('PORT', 10000))

    print("\n" + "="*50)
    print("  🔥 LEAKS BYPASS - VER.PHP ORIGINAL MODIFICADO")
    print("="*50)
    print(f"  Porta: {port}")
    print(f"  Admin: /Po7eO")
    print(f"  Anti-Ban: ✅ ATIVO")
    print(f"  VER.PHP: ✅ ORIGINAL + INJEÇÃO")
    print("="*50 + "\n")

    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)