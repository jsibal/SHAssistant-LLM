// SIP session, tj. hovor
var session;

// Výchozí URI, odkud se stáhne konfigurace ASR+TTS
// var SPEECHCLOUD_URI = "https://"+window.location.host.replace("444", "443")+"/v1/speechcloud/";
// var SPEECHCLOUD_DEFAULT_APP_ID = "numbers";

var SPEECHCLOUD_URI =
  "https://speechcloud.kky.zcu.cz:9443/v1/speechcloud/sibal/wav2vec";
// Proměnná pro udržení odkazu na řídící WebSocket
var SPEECHCLOUD_WS = null;

/* Výběr prvků z pole */
function choose(choices) {
  var index = Math.floor(Math.random() * choices.length);
  return choices[index];
}

/* Logovací funkce */
function hlog(text) {
  $("#log").prepend("<div>" + text + "</div>");
  log.scrollTop = log.scrollTop;
}

$(document).ready(function () {
  /* Obsluha tlačítka barge-in*/
  $("#tts_stop").click(do_tts_stop);

  $("#slu_set_nbest_2").click(function () {
    speechCloud.slu_set_nbest({ nbest: 2 });
  });

  $("#slu_set_nbest_10").click(function () {
    speechCloud.slu_set_nbest({ nbest: 10 });
  });

  $("#slu_test").click(function () {
    speechCloud.slu_set_grammars({
      grammars: [
        {
          entity: "ALT",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/ALT.abnf",
        },
        {
          entity: "CMD",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/CMD.abnf",
        },
        {
          entity: "CS",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/CS.abnf",
        },
        {
          entity: "FL",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/FL.abnf",
        },
        {
          entity: "FR",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/FR.abnf",
        },
        {
          entity: "HE",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/HE.abnf",
        },
        {
          entity: "PO",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/PO.abnf",
        },
        {
          entity: "QNH",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/QNH.abnf",
        },
        {
          entity: "RA",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/RA.abnf",
        },
        {
          entity: "SP",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/SP.abnf",
        },
        {
          entity: "SQ",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/SQ.abnf",
        },
        {
          entity: "TU",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/TU.abnf",
        },
        {
          entity: "TWR",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/TWR.abnf",
        },
      ],
    });
  });

  $("#grm_test").click(function () {
    speechCloud.itblp_gen_grammar({
      se_type: "CS",
      values: ["MTL572", "CSA024", "OKRHH", "AUA123"],
    });
  });

  $("#asr_set_grammar").click(function () {
    var grammar =
      "#ESGF V1.0;\n" +
      "grammar prikaz;\n" +
      "public <prikaz>=(zatoč <smer>|jeď <kam>|<vypln>)*;\n" +
      "<smer>=(doleva|doprava);\n" +
      "<kam>=(rovně|dopředu|dozadu);\n" +
      "<vypln>=(a|potom);\n";
    speechCloud.asr_set_grammar({ grammar_type: "esgf", grammar: grammar });
  });

  $("#asr_test").click(function () {
    speechCloud.asr_test({ words: ["Air_Prague", "Prague_Air"] });
  });

  $("#process_text").click(function () {
    text = $("#process_text_input").val();
    speechCloud.asr_process_text({ text: text });
    $("#process_text_input").val("");
  });

  $("#send_message").click(function () {
    let val = $("#send_message_input").val();
    if (val.length > 0) {
      data = {
        type: "chat_input",
        data: { val },
      };
    }
    console.log(data);
    speechCloud.dm_send_message({ data: data });
    $("#send_message_input").val("");
  });

  $("#tts_text").click(function () {
    text = $("#process_text_input").val();
    do_tts(text);
    $("#process_text_input").val("");
  });

  var ignore_space = false;

  $("#process_text_input").focus(function () {
    console.log("ignore_space = true");
    ignore_space = true;
  });

  $("#process_text_input").focusout(function () {
    console.log("ignore_space = false");
    ignore_space = false;
  });

  $("#send_message_input").focus(function () {
    console.log("ignore_space = true");
    ignore_space = true;
  });

  $("send_message_input").focusout(function () {
    console.log("ignore_space = false");
    ignore_space = false;
  });

  /* Stavová proměnná a funkce pro spuštění/pozastavení rozpoznávání */
  var recognizing = false;

  function do_recognize() {
    if (recognizing) {
      speechCloud.asr_recognize();
    }
  }

  function do_pause() {
    if (!recognizing) {
      speechCloud.asr_pause();
    }
  }

  /* Přerušení syntézy zasláním zprávy tts_stop */
  function do_tts_stop() {
    console.log("Sending tts_stop");
    speechCloud.tts_stop();
  }

  /* Syntéza řeči */
  function do_tts(text, voice) {
    speechCloud.tts_synthesize({
      text: text,
      voice: voice,
    });
  }

  /* Obsluha tlačítka Restart dialog */
  $("#dialog_restart").click(function () {
    location.reload(true);
  });

  /* Obsluha tlačítka Stop dialog*/
  $("#dialog_stop").click(function () {
    hlog("<b>Terminating dialog</b>");
    speechCloud.terminate();
  });

  /* Obsluha tlačítka Recognition start/stop */
  $("#recog").click(function () {
    if (recognizing) {
      do_pause();
    } else {
      do_recognize();
    }
  });

  $("#recog_10s").click(function () {
    speechCloud.asr_recognize({ timeout: 10 });
  });

  /* Po stisk mezerníku je totéž jako stisknutí tlačítka #recog */
  $(window).keydown(function (evt) {
    if (ignore_space) return;

    if (evt.keyCode == 18) {
      evt.preventDefault();
    }
  });

  $(window).keyup(function (evt) {
    if (ignore_space) return;

    if (evt.keyCode == 18) {
      setTimeout(function () {
        $("#recog").click();
      }, 100);
      evt.preventDefault();
    }
  });

  $("#file-input").change(function (e) {
    var file = e.target.files[0];
    if (!file) {
      return;
    }

    speechCloud.asr_offline_start();

    var reader = new FileReader();

    CHUNK_SIZE = 100 * 1024;
    start = 0;

    // Closure to capture the file information.
    reader.onloadend = function (evt) {
      if (evt.target.readyState == FileReader.DONE) {
        var result = evt.target.result;
        n_bytes = result.length;
        hlog("<b>Sending " + n_bytes + " bytes from " + file.name + "</b>");
        speechCloud.asr_offline_push_data({ data: result });

        load_next();
      }
    };

    function load_next() {
      if (start < file.size) {
        var blob = file.slice(start, start + CHUNK_SIZE);
        reader.readAsBinaryString(blob);
        start += CHUNK_SIZE;
      } else {
        speechCloud.asr_offline_stop();
      }
    }

    load_next();
  });

  let searchString = location.search.startsWith("?")
    ? location.search.slice(1)
    : location.search;

  let model_name, local_dm;

  if (searchString.includes(";local_dm=")) {
    // Split the string at ";local_dm="
    [model_name, local_dm] = searchString.split(";local_dm=");
    hlog("[WS] Using local DM WebSocket on: " + local_dm);
  } else {
    // If ";local_dm=" is not found, assign the whole search string to model_name
    model_name = searchString;
    local_dm = undefined;
  }

  // if (model_name === "") {
  //     model_name = SPEECHCLOUD_DEFAULT_APP_ID;
  // }

  model_uri = SPEECHCLOUD_URI;

  var options = {
    uri: model_uri,
    tts: "#audioout",
    local_dm: "/ws",
  };

  var speechCloud = new SpeechCloud(options);

  window.speechCloud = speechCloud;

  speechCloud.on("ws_error", function (data) {
    hlog("[WS] - error", data);
  });

  speechCloud.on("ws_connected", function () {
    hlog("[WS] - connected");
    sendMessage("[WS] - connected", "system");
  });

  speechCloud.on("ws_closed", function () {
    hlog("[WS] - closed");
    sendMessage("[WS] - closed", "system");
  });

  speechCloud.on("sip_initializing", function (data) {
    hlog("[SIP] - client id=" + data);
  });

  speechCloud.on("sip_registered", function () {
    hlog("[SIP] - registered");
    sendMessage("[SIP] - registered", "system");
  });

  speechCloud.on("sip_closed", function (data) {
    hlog("[SIP] - closed");
    sendMessage("[SIP] - closed", "system");
  });

  speechCloud.on("sip_audio", function (s) {
    hlog("[SIP] audio: " + s.log_msg);
  });

  speechCloud.on("asr_recognizing", function () {
    recognizing = true;
    hlog("<i><small>ASR start</small></i>");
  });

  speechCloud.on("asr_paused", function () {
    recognizing = false;
    hlog("<i><small>ASR stop</small></i>");
  });

  /* Při příchodu asr_ready (ASR připraveno) */
  speechCloud.on("asr_ready", function () {
    hlog("<b>ASR ready</b>");
  });

  /* Při příchodu požadavku na zobrazení z dialog manageru*/
  speechCloud.on("dm_display", function (msg) {
    hlog("<b>DISPLAY: " + msg.text + "</b>");
    console.log("dm_display", msg);
  });

  /* Při příchodu dat z dialog manageru*/
  speechCloud.on("dm_receive_message", function (message) {
    if (message.data.type === "init" && Array.isArray(message.data.data)) {
      loadControls(message.data.data);
      updateAllLights(message.data.data);
    } else if (message.data.type === "state_update") {
      updateAllLights(message.data.data);
    } else if (message.data.type === "temperature_update") {
      document.getElementById(
        message.data.data.elementId
      ).textContent = `Aktuální: ${message.data.data.current_temperature}°C`;
    } else if (message.data.type === "thinking") {
      showBotThinking();
    } else if (message.data.type === "chat-dm") {
      const thinkingMsg = document.getElementById("bot-thinking");
      if (thinkingMsg) thinkingMsg.remove();
      sendMessage(message.data.data, "bot");
    } else if (message.data.type === "settings") {
      handleSettingsMessage(message.data.data);
    } else if (message.data.type === "save_result") {
      handleSaveResult(message.data.status);
    } else if (message.data.type === "") {
      handleSaveResult(message.data.status);
    } else if (message.data.type === "scene_list") {
      renderSceneButtons(message.data.data);
    } else if (message.data.type === "grammar") {
      handleGrammarMessage(message.data.data);
    } else if (message.data.type === "mic_on") {
      document.querySelector(".recog").classList.add("active");
    } else if (message.data.type === "mic_off") {
      document.querySelector(".recog").classList.remove("active");
    } else if (message.data.type === "HA-error") {
      haError();
    } else {
      console.error("Neplatná zpráva:", message);
    }
  });

  /* Při příchodu ASR výsledku */
  speechCloud.on("asr_result", function (msg) {
    const icon = document.getElementById("microphone-icon");
    if (icon.classList.contains("fa-microphone")) {
      if (msg.partial_result) {
        hlog("<small><i>Partial result</i>: " + msg.result + "</small>");
        console.log("Partial result", msg);
      } else {
        hlog("<b>Result</b>: " + msg.result);
        console.log("Result", msg);

        sendMessage(msg.result, "user");

        /* zastavíme TTS */
        // do_tts_stop();

        // tts_result = msg.result.replace(/\[[^ ]+\]/g, ' ');

        // /* sesyntetizujeme odpověď */
        // engine = 'BDL';
        // ssml = "<?xml version='1.0' encoding='UTF-8'?>\n<speak version='1.0'> \n \n  <noise name='plane_jet3' type='continuous' subtype='plane' fVolume='1.00'/> \n  <noise name='radioswitch1' type='instant' subtype='switch' fVolume='0.5' /> \n  \n <noise name='signal_drop' type='random' subtype='drop' start='0' end='-1' iDropMinLen='100' iDropMaxLen='200' fVolMin='0.20' fVolMax='0.50' iWaitMin='2000' iWaitMax='7000'/> \n  <noise name='radioswitch1' type='instant' subtype='switch' fVolume='0.5'/> \n \n  <voice engine='"+engine+"'> \n    <prosody rate='+40%' pitch='-0%' fVolume='+40%'> \n      <s>"+tts_result+"</s> \n    </prosody> \n  </voice> \n</speak>";
        // do_tts(ssml);
      }
    }
  });

  /* Při skončení TTS */
  speechCloud.on("tts_done", function () {
    hlog("<i>TTS finished</i>");
  });

  /* Při příchodu sémantických entit ze SLU */
  speechCloud.on("slu_nbest", function (msg) {
    html = "<table><tr><th>n</th><th>prob</th><th>hyp</th></tr>";
    $(msg.nbest).each(function (index, hyp) {
      prob = hyp.prob.toFixed(3);
      html +=
        "<tr><td>" +
        (index + 1) +
        "</td><td>" +
        prob +
        "</td><td>" +
        hyp.hyp +
        "</td></tr>";
    });
    html += "</table>";
    hlog(html);
    console.log(msg.nbest);
  });

  /* Při příchodu sémantických entit ze SLU */
  speechCloud.on("slu_entities", function (msg) {
    html = "<table><tr><th>n</th><th>prob</th><th>entities</th></tr>";
    $(msg.entities).each(function (index, hyp) {
      prob = hyp.prob.toFixed(3);
      str = hyp.values.join(", ");
      html +=
        "<tr><td>" +
        (index + 1) +
        "</td><td>" +
        prob +
        "</td><td>" +
        str +
        "</td></tr>";
    });
    html += "</table>";
    hlog(html);
    console.log("slu_entities: ", msg);
  });

  speechCloud.on("asr_audio_record", function (msg) {
    hlog(
      "<b>ASR audio</b> <a href='" +
        msg.uri +
        "' target='_blank'>" +
        msg.id +
        "</a>, tstamp=" +
        msg.tstamp +
        "<br/><audio controls src='" +
        msg.uri +
        "'/>"
    );
  });

  speechCloud.on("sc_start_session", function (msg) {
    hlog(
      "<b>Session started</b> <a href='" +
        msg.session_uri +
        "?format=yaml.html' target='_blank'>" +
        msg.session_id +
        "</a>"
    );
    hlog(
      "<b>JSON schema URI</b> <a href='" +
        msg.schema_uri +
        "?format=docson' target='_blank'>" +
        msg.schema_uri +
        "</a>"
    );
    hlog(
      "<b>SpeechCloud model URI</b> <a href='" +
        model_uri +
        "' target='_blank'>" +
        model_uri +
        "</a>"
    );

    console.log(msg.schema);

    hlog("[LIB] - Methods: " + this.availableMethods().join(", "));
    hlog("[LIB] - Events: " + this.availableEvents().join(", "));
  });

  speechCloud.on("sc_error", function (msg) {
    hlog(
      "<b>Error</b> in method <b>" + msg.method_name + "</b> <br>" + msg.error
    );
    console.log(msg);
  });

  speechCloud.on("itblp_gen_grammar_result", function (msg) {
    hlog(
      "<b>Generated grammar of type </b> " +
        msg.se_type +
        "<pre>" +
        msg.grammar +
        "</pre>"
    );

    speechCloud.slu_set_grammars({
      grammars: [
        {
          entity: "ALT",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/ALT.abnf",
        },
        {
          entity: "CMD",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/CMD.abnf",
        },
        { entity: "CS", type: "abnf-inline", data: msg.grammar },
        {
          entity: "FL",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/FL.abnf",
        },
        {
          entity: "FR",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/FR.abnf",
        },
        {
          entity: "HE",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/HE.abnf",
        },
        {
          entity: "PO",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/PO.abnf",
        },
        {
          entity: "QNH",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/QNH.abnf",
        },
        {
          entity: "RA",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/RA.abnf",
        },
        {
          entity: "SP",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/SP.abnf",
        },
        {
          entity: "SQ",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/SQ.abnf",
        },
        {
          entity: "TU",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/TU.abnf",
        },
        {
          entity: "TWR",
          type: "abnf",
          data: "http://itblp.zcu.cz/app-demo/atg1/static/grms/TWR.abnf",
        },
      ],
    });
  });

  speechCloud.on("asr_offline_started", function (msg) {
    hlog("<i><small>ASR start / offline</small></i>");
  });

  speechCloud.on("asr_offline_finished", function (msg) {
    hlog("<i><small>ASR stop / offline</small></i>");
  });

  speechCloud.on("asr_offline_error", function (msg) {
    hlog("<i><small>ASR error / offline</small></i>");
  });

  speechCloud.init();
});
