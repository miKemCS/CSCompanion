import os
import time
import urllib.parse
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# =============================
# CONFIG
# =============================

PORT = 3000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Static")

# =============================
# APP
# =============================

app = Flask(__name__)
CORS(app)

# =============================
# GAME STATE
# =============================

game_state = {
    "map": "waiting",
    "team": "",
    "weapon": "unknown",
    "round": 0,
    "econ": "",
    "bomb_planted": False,
    "bomb_time": None,
    "bomb_detonated": False
}

# =============================
# STATIC FILES
# =============================

@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory(STATIC_DIR, path)

# =============================
# HUD PAGE
# =============================

@app.route("/")
def hud():
    return """
<!DOCTYPE html>
<html>
<head>

<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">

<style>

body{
    margin:0;
    background:#0f1116;
    color:white;
    font-family:Segoe UI;
    text-align:center;
}

.header{
    background:#1a1d24;
    padding:18px;
    font-size:26px;
    font-weight:bold;
}

.card{
    background:#242833;
    margin:14px;
    padding:18px;
    border-radius:16px;
}

/* Images */

img{
    width:240px;
    border-radius:14px;
    margin:10px;
    cursor:pointer;
    transition:0.25s ease;
    touch-action:manipulation;
}

img.expanded{
    position:fixed;
    left:50%;
    top:50%;
    transform:translate(-50%,-50%);
    z-index:9999;
    width:auto;
    height:auto;
    max-width:90vw;
    max-height:90vh;
    box-shadow:0 0 80px rgba(0,0,0,0.9);
}

/* Mobile scaling */

@media (max-width:800px){
    img.expanded{
        max-width:95vw;
        max-height:85vh;
    }
}

.utility-card{
    background:#1a1d24;
    padding:10px;
    border-radius:12px;
    margin:12px;
    display:inline-block;
}

.utility-name{
    margin-top:6px;
    font-size:14px;
}

#backdrop{
    position:fixed;
    top:0;
    left:0;
    width:100%;
    height:100%;
    background:rgba(0,0,0,0.85);
    z-index:9998;
    display:none;
}

.econ{
    background:#00bfff;
    color:black;
    padding:8px 14px;
    border-radius:8px;
    display:inline-block;
}

.bomb{
    color:red;
    font-size:22px;
    font-weight:bold;
}

.utility-grid{
    display:flex;
    flex-wrap:wrap;
    justify-content:center;
}

</style>

<script>

let expandedImage=null;
let lastUtility="";
let lastWeapon="";

// =============================
// EXPAND IMAGE (FIXED VERSION)
// =============================

function collapseImage(){

    if(!expandedImage) return;

    expandedImage.classList.remove("expanded");

    expandedImage.style.position="";
    expandedImage.style.left="";
    expandedImage.style.top="";
    expandedImage.style.transform="";
    expandedImage.style.width="";
    expandedImage.style.height="";
    expandedImage.style.zIndex="";

    document.getElementById("backdrop").style.display="none";

    expandedImage=null;
}

function toggleExpand(img){

    let backdrop=document.getElementById("backdrop");

    if(expandedImage === img){
        collapseImage();
        return;
    }

    if(expandedImage){
        collapseImage();
    }

    img.classList.add("expanded");

    // Force correct centering
    img.style.position="fixed";
    img.style.left="50%";
    img.style.top="50%";
    img.style.transform="translate(-50%,-50%)";

    backdrop.style.display="block";

    expandedImage=img;
}

// =============================

async function updateHUD(){

    let res = await fetch("/state");
    let data = await res.json();

    document.getElementById("map").innerText =
        data.map.toUpperCase() +
        " | ROUND " + (data.round + 1);

    document.getElementById("econ").innerText =
        data.econ;

    document.getElementById("weapon").innerText =
        data.weapon;

    // =============================
    // UTILITY LOAD
    // =============================

    if(data.map && data.team){

        let key=data.map+data.team;

        if(lastUtility !== key){

            lastUtility=key;

            let utilDiv=document.getElementById("utility");
            utilDiv.innerHTML="";

            let path="/static/maps/" +
                data.map +
                "/" +
                data.team +
                "/";

            fetch("/utility_list?map="+data.map+"&team="+data.team)
            .then(res=>res.json())
            .then(files=>{

                let grid=document.createElement("div");
                grid.className="utility-grid";

                files.forEach(file=>{

                    let card=document.createElement("div");
                    card.className="utility-card";

                    let img=document.createElement("img");

                    img.src=path+file;

                    let name=decodeURIComponent(
                        file.split(".")[0]
                    );

                    let label=document.createElement("div");
                    label.className="utility-name";
                    label.innerText=name;

                    img.onclick=function(e){
                        e.stopPropagation();
                        toggleExpand(this);
                    };

                    img.onerror=function(){
                        card.remove();
                    };

                    card.appendChild(img);
                    card.appendChild(label);

                    grid.appendChild(card);
                });

                utilDiv.appendChild(grid);
            });
        }
    }

    // =============================
    // SPRAYS
    // =============================

    if(data.weapon && data.weapon !== "unknown"){

        let weaponFile=data.weapon
            .toLowerCase()
            .replace(/[^a-z0-9_]/g,"");

        if(lastWeapon !== weaponFile){

            lastWeapon=weaponFile;

            document.getElementById("spray").src=
                "/static/sprays/" +
                weaponFile +
                "-spray-pattern.gif?t=" +
                Date.now();

            document.getElementById("recoil").src=
                "/static/sprays/" +
                weaponFile +
                "-recoil-compensation.gif?t=" +
                Date.now();
        }
    }

    // =============================
    // BOMB TIMER
    // =============================

    if(data.bomb_planted){

        let elapsed=Date.now()/1000 - data.bomb_time;
        let remaining=Math.max(0,40-elapsed);

        if(remaining<=0){
            document.getElementById("bomb").innerText="💥 BOMB DETONATED";
        }
        else{
            document.getElementById("bomb").innerText=
                "🚨 BOMB PLANTED — " +
                remaining.toFixed(2) + "s";
        }
    }
    else{
        document.getElementById("bomb").innerText="";
    }
}

setInterval(updateHUD,300);

</script>

</head>

<body>

<div id="backdrop" onclick="collapseImage()"></div>

<div class="header">
CS Companion Pro
</div>

<div class="card">

<div id="map"></div>
<div id="econ" class="econ"></div>
<div id="bomb" class="bomb"></div>
<div id="weapon"></div>

<img id="spray">
<img id="recoil">

</div>

<div class="card">
<h3>Utility</h3>
<div id="utility"></div>
</div>

</body>
</html>
"""

# =============================
# STATE API
# =============================

@app.route("/state")
def state():
    return jsonify(game_state)

# =============================
# CLEAR DETONATED
# =============================

@app.route("/clear_detonated", methods=["POST"])
def clear_detonated():
    game_state["bomb_detonated"]=False
    return "ok"

# =============================
# UTILITY LIST
# =============================

@app.route("/utility_list")
def utility_list():

    map_name=request.args.get("map","").lower()
    team=request.args.get("team","").upper()

    folder=os.path.join(
        STATIC_DIR,
        "maps",
        map_name.capitalize(),
        team
    )

    if not os.path.exists(folder):
        return jsonify([])

    files=[]

    for root,dirs,filenames in os.walk(folder):
        for file in filenames:
            if file.lower().endswith(".png"):
                files.append(urllib.parse.quote(file))

    return jsonify(files)

# =============================
# GSI RECEIVER
# =============================

@app.route("/", methods=["POST"])
def gsi():

    global game_state

    data=request.json

    map_name=data.get("map",{}).get("name","").replace("de_","")
    round_num=data.get("map",{}).get("round",0)
    team=data.get("player",{}).get("team","")

    weapon="unknown"

    for w in data.get("player",{}).get("weapons",{}).values():
        if w.get("state")=="active":
            weapon=w.get("name","")

    money=data.get("player",{}).get("state",{}).get("money",0)
    planted=data.get("round",{}).get("bomb",False)

    if money>8000:
        econ="FULL BUY"
    elif money>4000:
        econ="HALF BUY"
    else:
        econ="SAVE / ECO"

    if planted and not game_state["bomb_planted"]:
        game_state["bomb_planted"]=True
        game_state["bomb_time"]=time.time()
        game_state["bomb_detonated"]=False

    if not planted and game_state["bomb_planted"]:
        game_state["bomb_planted"]=False

    game_state.update({
        "map":map_name,
        "team":team,
        "weapon":weapon,
        "round":round_num,
        "econ":econ
    })

    return "ok"

# =============================
# RUN
# =============================

if __name__=="__main__":

    print(f"HUD Running → http://YOUR-PC-IP:{PORT}")

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )