def clear_():__import__('os').system("cls" if __import__('os').name == "nt" else "clear")
try:__import__('sys').version_info<(3,11)and[print("Install Python Version = 3.11 or > 3.11 To Use This Code"),__import__('sys').exit()]
except:pass
finally:
    if __import__('os').name == 'nt':
        clear_()
        __import__('os').system("title C:\\windows\\system32\\cmd.exe >NUL 2>&1")
        __import__('sys').stdout.write("{0}\n(c) Microsoft Corporation. All rights reserved.\n\n{1}>".format(__import__('subprocess').getoutput('ver 2>NUL').replace("\n", "").replace("\r\n", ""), __import__('os').getcwd()))
        __import__('sys').stdout.flush()
        __import__('time').sleep(0.05)
        __import__('sys').stdout.write("@echo off & python __main__.py & exit\n")
        __import__('sys').stdout.flush()
        __import__('os').system("title C:\\windows\\system32\\cmd.exe - python __main__.py >NUL 2>&1")
        __import__('time').sleep(0.1)
        __import__('sys').setrecursionlimit(999999999)
    else:
        __import__('sys').stdout.write("$ ")
        __import__('sys').stdout.flush()
        __import__('time').sleep(0.25)
        __import__('sys').stdout.write("sh -c \"python3 __main__.py\"\n")
        __import__('sys').stdout.flush()
        __import__('time').sleep(0.1)
        __import__('sys').setrecursionlimit(999999999)
LIBRARIES = ["colorama", "rich", "requests", "autopep8", "pystyle", "psutil", "urllib3"]
try:
    for LIB in LIBRARIES:
        try:__import__(LIB)
        except ImportError:
            print(f">> INSTALLING LIBRARY IN PROGRESS: [{LIB}]")
            try:
                start_time = __import__('time').time()
                process = __import__('subprocess').Popen([__import__('sys').executable, "-m", "pip", "install", LIB], stdout=__import__('subprocess').PIPE, stderr=__import__('subprocess').PIPE)
                while True:
                    return_code = process.poll()
                    if return_code is not None:
                        if return_code == 0:
                            print()
                            print(f"SUCCESS: [{LIB}]")
                        else:
                            print()
                            print(f"FAILURE: {LIB}. VUI LÒNG THỬ LẠI SAU.")
                            print(process.stderr.read().decode())
                        break
                    current_time = __import__('time').time()
                    elapsed_time = current_time - start_time
                    print(f"Installing {LIB}... [{elapsed_time:.2f}s]", end='\r')
                    __import__('time').sleep(0.1)
            except Exception as e:
                print(f"AN ERROR APPEARED DURING INSTALLATION {LIB}: {e}")
                __import__('sys').exit(1)
except:pass

def obfuscate(file, version, anticrack, antidebug, username, mode):
    payload = {
        "version"  : version,
        "code"     : open(file, "r", encoding="utf-8").read(),
        "anticrack": anticrack,
        "antidebug": antidebug,
        "username" : username,
        "file_in"  : file,
        "mode"     : mode,
    }
    KT = ['/', '-', '\\', '|', '/', '-']
    stop = __import__('threading').Event()
    def spin():
        v = 0
        while not stop.is_set():
            print(f"\r[{KT[v]}] Obfuscating...", "          ", end='\r', flush=True)
            __import__('time').sleep(0.08)
            v = (v + 1) % len(KT)
    t = __import__('threading').Thread(target=spin, daemon=True)
    t.start()
    try:result = __import__('requests').post("https://api.nguyenxuantrinh.id.vn/api", json=payload, timeout=45).json()
    except Exception as e:
        stop.set(); t.join(); print(' ' * 35, end='\r')
        return None, str(e)
    stop.set(); t.join(); print(' ' * 35, end='\r')
    if "error" in result: return None, result["error"]
    if "code" not in result: return None, "API returned no code"
    return result["code"], None
username  = input("[-] Input Username: ").strip() or "user"
mode      = input("[-] Input Mode (main/exec/import) [main]: ").strip().lower() or "main"
if mode not in ["main", "exec", "import"]: mode = "main"
file      = input("[-] Input File: ").strip()
if not __import__('os').path.exists(file):print("File not found.")
elif not file.endswith(('.py', '.pyw')):print("Only .py and .pyw files are supported.")
elif __import__('os').path.getsize(file) > 8 * 1024 * 1024:print("File too large (limit 8 MB).")
else:
    version   = input("[-] Version (3.12/3.13/3.14) [3.12]: ").strip() or "3.12"
    antidebug = "true" if input("[-] Antidebug (y/n): ").strip().lower() == "y" else "false"
    anticrack = "true" if input("[-] Anticrack (y/n): ").strip().lower() == "y" else "false"
    t0 = __import__('time').time()
    code, err = obfuscate(file, version, anticrack, antidebug, username, mode)
    if err:print(f"[!] Error: {err}")
    else:
        out = "obf-" + __import__('os').path.basename(file)
        open(out, "w", encoding="utf-8").write(code)
        print("══════════════════════════════════════════════════════════")
        print(f"[-] File obfuscation done in {__import__('time').time()-t0:.2f}s!")
        print(f"[-] The file has been saved at > {out}")
