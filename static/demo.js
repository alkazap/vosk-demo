// Global UI elements:
//  - log: event log
//  - trans: transcription window

// Global objects:
//  - tt: simple structure for managing the list of hypotheses
//  - dictate: dictate object with control methods 'init', 'startListening', ...
//       and event callbacks onResults, onError, ...
var output = document.getElementById('output')

var tt = new Transcription();

var dictate = new Dictate({
		server : "ws://localhost:20005/webclient",
		recorderWorkerPath : '../static/lib/recorderWorker.js',
		onReadyForSpeech : function() {
			__message("READY FOR SPEECH");
			__status("Listening and transcribing...");
		},
		onEndOfSpeech : function() {
			__message("END OF SPEECH");
			__status("Transcribing...");
		},
		onEndOfSession : function() {
			__message("END OF SESSION");
			__status("");
		},
		onPartialResults : function(res) {
			// TODO: demo the case where there are more hypos
			tt.add(res.partial, false);
			__updateTranscript(tt.toString());
		},
		onResults : function(res) {
			// TODO: demo the case where there are more results
			// let wordCount = res.result.length;
			// let responseTime = res.result[wordCount-1].end - res.result[0].start;
			// let text = `[${responseTime.toPrecision(2)}]:`;
			// for (let i = 0; i < wordCount; i++) {
			// 	let responseTime = res.result[i].end - res.result[i].start;
			// 	text += ` [${responseTime.toPrecision(2)}]${res.result[i].word}`;
			// }
			// text += '\n';
			tt.add(res.text, true);
			__updateTranscript(tt.toString());
			// diff() is defined only in diff.html
			if (typeof(diff) == "function") {
				diff();
			}
		},
		onError : function(code, data) {
			__error(code, data);
			__status("Error: " + code);
			dictate.cancel();
		},
		onEvent : function(code, data) {
			__message(code, data);
		}
	});

// Private methods (called from the callbacks)
function __message(code, data) {
	log.innerHTML = "msg: " + code + ": " + (data || '') + "\n" + log.innerHTML;
}

function __error(code, data) {
	log.innerHTML = "ERR: " + code + ": " + (data || '') + "\n" + log.innerHTML;
}

function __status(msg) {
	statusBar.innerHTML = msg;
}

function __serverStatus(msg) {
	serverStatusBar.innerHTML = msg;
}

function __updateTranscript(text) {
	// $("#trans").val(text);
	output.textContent = text;
}

// Public methods (called from the GUI)
function toggleLog() {
	$(log).toggle();
}
function clearLog() {
	log.innerHTML = "";
}

function clearTranscription() {
	tt = new Transcription();
	// $("#trans").val("");
	output.textContent = "";
}

function startListening() {
	dictate.startListening();
}

function stopListening() {
	dictate.stopListening();
}

function cancel() {
	dictate.cancel();
}

function init() {
	dictate.init();
}

function showConfig() {
	var pp = JSON.stringify(dictate.getConfig(), undefined, 2);
	log.innerHTML = pp + "\n" + log.innerHTML;
	$(log).show();
}

window.onload = function() {
	init();
};
