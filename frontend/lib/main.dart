import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:file_picker/file_picker.dart';

void main() {
  runApp(const SwarmBharatApp());
}

class SwarmBharatApp extends StatelessWidget {
  const SwarmBharatApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SwarmBharat AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1A73E8)),
        useMaterial3: true,
      ),
      home: const ChatScreen(),
    );
  }
}

class ChatMessage {
  final String text;
  final bool isUser;
  ChatMessage({required this.text, required this.isUser});
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  // ─────────────────────────────────────────────────────────────────────────
  // BUG FIX 1: Use 127.0.0.1 — never "localhost" in Flutter Web on Chrome.
  // Chrome treats them differently for CORS. "localhost" triggers a pre-flight
  // failure that shows as "could not connect to server".
  // ─────────────────────────────────────────────────────────────────────────
  static const String _backendUrl = 'http://127.0.0.1:8000/swarm';

  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;
  String _mode = 'personal';

  // Voice
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isListening = false;

  // File
  PlatformFile? _currentFile;

  Future<void> _sendQuery(String query) async {
    if (query.trim().isEmpty) return;

    setState(() {
      _messages.add(ChatMessage(text: query, isUser: true));
      _isLoading = true;
    });
    _controller.clear();
    _scrollToBottom();

    try {
      // ───────────────────────────────────────────────────────────────────
      // BUG FIX 2: Flutter Web (Chrome) blocks MultipartRequest to 127.0.0.1
      // due to a known issue with the browser http implementation.
      //
      // Solution: Send as multipart but use the correct 127.0.0.1 URL, AND
      // we add the file as bytes (not path) because Flutter Web has no file
      // system paths — only bytes from the file picker.
      // ───────────────────────────────────────────────────────────────────
      var request = http.MultipartRequest(
        'POST',
        Uri.parse(_backendUrl),
      );

      // These match the FastAPI Form() parameter names exactly
      request.fields['query'] = query.trim();
      request.fields['mode'] = _mode;

      // Attach file bytes if a file was picked (Flutter Web uses bytes, not path)
      if (_currentFile != null && _currentFile!.bytes != null) {
        request.files.add(
          http.MultipartFile.fromBytes(
            'file',                           // matches FastAPI: file: UploadFile = File(None)
            _currentFile!.bytes!,
            filename: _currentFile!.name,
          ),
        );
      }

      // ───────────────────────────────────────────────────────────────────
      // BUG FIX 3: Set a long timeout. The 7-agent swarm takes 60-120 seconds.
      // Without this, the default timeout drops the connection and you see
      // "could not connect to server" even though the backend is working fine.
      // ───────────────────────────────────────────────────────────────────
      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 180),
        onTimeout: () => throw Exception(
          'Request timed out after 3 minutes. The swarm is still thinking — try a simpler question.',
        ),
      );

      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        // "response" matches what the FastAPI backend returns
        final answer = data['response'] ?? 'No answer received.';

        setState(() {
          _messages.add(ChatMessage(text: answer, isUser: false));
          _currentFile = null; // clear file after successful send
        });
      } else {
        // Show the full error body for debugging — very useful for beginners
        setState(() {
          _messages.add(ChatMessage(
            text: 'Server returned error ${response.statusCode}.\n\nDetails: ${response.body}',
            isUser: false,
          ));
        });
      }
    } on Exception catch (e) {
      setState(() {
        _messages.add(ChatMessage(
          text: 'Connection error: $e\n\n'
              'Checklist:\n'
              '1. Is backend running? (uvicorn main:app --reload)\n'
              '2. Does terminal show "Application startup complete"?\n'
              '3. Can you open http://127.0.0.1:8000 in Chrome?\n'
              '4. Check if any firewall is blocking port 8000.',
          isUser: false,
        ));
      });
    } finally {
      setState(() => _isLoading = false);
      _scrollToBottom();
    }
  }

  // ── Voice input ───────────────────────────────────────────────────────────
  void _startListening() async {
    bool available = await _speech.initialize(
      onError: (error) {
        setState(() => _isListening = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Voice error: ${error.errorMsg}')),
        );
      },
    );
    if (available) {
      setState(() => _isListening = true);
      _speech.listen(
        onResult: (SpeechRecognitionResult result) {
          if (result.finalResult) {
            setState(() => _isListening = false);
            if (result.recognizedWords.isNotEmpty) {
              _sendQuery(result.recognizedWords);
            }
          }
        },
        localeId: 'te_IN', // Telugu — change to 'hi_IN' for Hindi, 'en_IN' for English
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Microphone permission needed. Allow it in Chrome settings.')),
      );
    }
  }

  void _stopListening() {
    _speech.stop();
    setState(() => _isListening = false);
  }

  // ── File picker (Flutter Web: uses bytes, not file path) ─────────────────
  Future<void> _pickFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'txt'],
      withData: true, // IMPORTANT: withData=true gives us bytes for Flutter Web
    );
    if (result != null && result.files.isNotEmpty) {
      setState(() {
        _currentFile = result.files.first;
        _messages.add(ChatMessage(
          text: 'Attached: ${_currentFile!.name} (${(_currentFile!.size / 1024).toStringAsFixed(1)} KB)',
          isUser: true,
        ));
      });
      _scrollToBottom();
    }
  }

  void _clearFile() {
    setState(() => _currentFile = null);
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  // ── UI ────────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0F4F8),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1A73E8),
        foregroundColor: Colors.white,
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('SwarmBharat AI', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text('Telugu · Hindi · English', style: TextStyle(fontSize: 11, color: Colors.white70)),
          ],
        ),
        actions: [
          // Mode toggle
          GestureDetector(
            onTap: () => setState(() {
              _mode = _mode == 'personal' ? 'business' : 'personal';
            }),
            child: Container(
              margin: const EdgeInsets.only(right: 12),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white24,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                _mode == 'personal' ? 'Personal' : 'Business',
                style: const TextStyle(color: Colors.white, fontSize: 13),
              ),
            ),
          ),
          if (_currentFile != null)
            IconButton(
              icon: const Icon(Icons.attach_file, color: Colors.white),
              tooltip: 'Clear attached file',
              onPressed: _clearFile,
            ),
        ],
      ),

      body: Column(
        children: [
          // Mode banner
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 5, horizontal: 16),
            color: _mode == 'personal'
                ? const Color(0xFFE8F5E9)
                : const Color(0xFFE3F2FD),
            child: Text(
              _mode == 'personal'
                  ? 'Personal mode — farmers, students, daily workers'
                  : 'Business mode — IT / RFP professionals',
              style: TextStyle(
                fontSize: 12,
                color: _mode == 'personal'
                    ? const Color(0xFF2E7D32)
                    : const Color(0xFF1565C0),
              ),
            ),
          ),

          // Attached file indicator
          if (_currentFile != null)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 16),
              color: const Color(0xFFFFF8E1),
              child: Row(
                children: [
                  const Icon(Icons.picture_as_pdf, size: 16, color: Color(0xFFE65100)),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      '${_currentFile!.name} — will be sent with your next message',
                      style: const TextStyle(fontSize: 12, color: Color(0xFFE65100)),
                    ),
                  ),
                  GestureDetector(
                    onTap: _clearFile,
                    child: const Icon(Icons.close, size: 16, color: Color(0xFFE65100)),
                  ),
                ],
              ),
            ),

          // Messages
          Expanded(
            child: _messages.isEmpty
                ? _buildWelcome()
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length + (_isLoading ? 1 : 0),
                    itemBuilder: (ctx, i) {
                      if (i == _messages.length) return _buildThinking();
                      return _buildBubble(_messages[i]);
                    },
                  ),
          ),

          // Input bar
          _buildInputBar(),
        ],
      ),
    );
  }

  Widget _buildWelcome() {
    final tips = _mode == 'personal'
        ? [
            'పంట వేసే సమయం ఎప్పుడు బాగుంటుంది?',
            'PM Kisan yojana ke liye apply kaise karein?',
            'How to get a student loan in India?',
            'Resume improve kaise karein? (Upload your PDF resume)',
          ]
        : [
            'How to write an executive summary for an IT RFP?',
            'What are the key pricing strategies for software bids?',
          ];

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const Icon(Icons.hub, size: 60, color: Color(0xFF1A73E8)),
            const SizedBox(height: 12),
            const Text('SwarmBharat AI',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            const Text('7 AI agents working together for you',
                style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 24),
            ...tips.map((t) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: InkWell(
                    onTap: () => _sendQuery(t),
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                            color: const Color(0xFF1A73E8).withOpacity(0.25)),
                      ),
                      child: Text(t, style: const TextStyle(fontSize: 13)),
                    ),
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Widget _buildBubble(ChatMessage msg) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        mainAxisAlignment:
            msg.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!msg.isUser) ...[
            const CircleAvatar(
              radius: 15,
              backgroundColor: Color(0xFF1A73E8),
              child: Icon(Icons.hub, size: 16, color: Colors.white),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: msg.isUser ? const Color(0xFF1A73E8) : Colors.white,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft:
                      Radius.circular(msg.isUser ? 16 : 4),
                  bottomRight:
                      Radius.circular(msg.isUser ? 4 : 16),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.06),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  )
                ],
              ),
              child: Text(
                msg.text,
                style: TextStyle(
                  color: msg.isUser ? Colors.white : Colors.black87,
                  fontSize: 14,
                  height: 1.5,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildThinking() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          const CircleAvatar(
            radius: 15,
            backgroundColor: Color(0xFF1A73E8),
            child: Icon(Icons.hub, size: 16, color: Colors.white),
          ),
          const SizedBox(width: 8),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
                const SizedBox(width: 10),
                Text(
                  '7 agents thinking... (may take 1-2 min)',
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(8, 6, 8, 12),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
              color: Colors.black.withOpacity(0.07),
              blurRadius: 8,
              offset: const Offset(0, -2))
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            // Mic button
            IconButton(
              icon: Icon(
                _isListening ? Icons.mic_off : Icons.mic,
                color: _isListening ? Colors.red : const Color(0xFF1A73E8),
              ),
              tooltip: _isListening ? 'Stop listening' : 'Speak your question',
              onPressed: _isLoading
                  ? null
                  : (_isListening ? _stopListening : _startListening),
            ),

            // File attach button
            IconButton(
              icon: Icon(
                Icons.attach_file,
                color: _currentFile != null
                    ? Colors.orange
                    : const Color(0xFF1A73E8),
              ),
              tooltip: 'Attach PDF or text file',
              onPressed: _isLoading ? null : _pickFile,
            ),

            // Text input
            Expanded(
              child: TextField(
                controller: _controller,
                enabled: !_isLoading,
                decoration: InputDecoration(
                  hintText: _isListening
                      ? 'Listening...'
                      : 'Type or speak in Telugu, Hindi, English...',
                  hintStyle:
                      const TextStyle(fontSize: 13, color: Colors.grey),
                  filled: true,
                  fillColor: const Color(0xFFF5F7FA),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide.none,
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 10),
                ),
                onSubmitted:
                    _isLoading ? null : (t) => _sendQuery(t),
                maxLines: null,
                textInputAction: TextInputAction.send,
              ),
            ),

            // Send button
            const SizedBox(width: 6),
            FloatingActionButton.small(
              onPressed: _isLoading
                  ? null
                  : () => _sendQuery(_controller.text),
              backgroundColor: _isLoading
                  ? Colors.grey[300]
                  : const Color(0xFF1A73E8),
              elevation: 0,
              child: Icon(
                _isLoading ? Icons.hourglass_empty : Icons.send,
                color: Colors.white,
                size: 18,
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}