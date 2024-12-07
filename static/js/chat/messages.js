$(document).ready(function() {
    let send_message_form = $('#send-message-form');
    let input_message = $('.input-message');
    let image = $('.profile-pic').attr('src');
    const USER_ID = $('#logged-in-user').val();

    // Setup WebSocket
    let locn = window.location;
    let wsStart = (locn.protocol === 'https:') ? 'wss://' : 'ws://';
    let endpoint = wsStart + locn.host + '/chat/';
    var chatSocket = new WebSocket(endpoint);

    chatSocket.onopen = function() {
        console.log('WebSocket connection established');

        // Handle the form submission for sending messages
        send_message_form.on('submit', function(e) {
            e.preventDefault();
            let message = input_message.val().trim();
            if (!message) return; // Prevent sending empty messages
            let send_to = get_active_other_user_id();
            let thread_id = get_active_thread_id();

            // Create the data object to send
            let data = {
                'message': message,
                'sent_by': USER_ID,
                'sent_to': send_to,
                'thread_id': thread_id
            };
            console.log('Sending message:', data);
            chatSocket.send(JSON.stringify(data));

            // Clear the input field
            input_message.val('');
        });
    };

    chatSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log('Message received:', data);
        newMessage(data.sent_by, data.message, data.thread_id);
    };

    chatSocket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };

    chatSocket.onclose = function(event) {
        console.log('WebSocket connection closed:', event);
    };

    function newMessage(sent_by, message, thread_id) {
        if ($.trim(message) === '') {
            return false; // Prevent empty messages from being displayed
        }
    
        let messageClass = (sent_by == USER_ID) ? 'sent' : 'received';
        let messageElement = `
            <div class="chat-msg ${messageClass}">
                <div class="chat-msg-profile">
                    <img class="chat-msg-img" src="${image}" alt="">
                    <div class="chat-msg-date"></div>
                </div>
                <div class="chat-msg-content">
                    <div class="chat-msg-text">${message}</div>
                </div>
            </div>`;

        console.log(image)
    
        // Ensure you're using the correct thread ID
        let chat_id = "chat_" + thread_id;
        let messageBody = $('.message-wrapper[chat-id="' + chat_id + '"] .chat-area-main');
    
        // Check if the message body was found
        if (messageBody.length === 0) {
            console.warn("No message body found for chat ID:", chat_id);
            return;
        }
    
        // Append the new message
        messageBody.append($(messageElement));
    
        // Only scroll if this chat area is active
        if ($('.message-wrapper.is_active').attr('chat-id') === chat_id) {
            messageBody.animate({
                scrollTop: messageBody.prop("scrollHeight")
            }, 100);
        }
    }
    
        // Handle click on contact
    $('.contact-li').on('click', function() {
        $('.conversation-area .active').removeClass('active');
        $(this).addClass('active');

        let chat_id = $(this).attr('chat-id');
        $('.message-wrapper.is_active').removeClass('is_active');
        $('.message-wrapper[chat-id="' + chat_id + '"]').addClass('is_active');

        // Optionally scroll to the top of the chat area when switching
        let activeMessageBody = $('.message-wrapper[chat-id="' + chat_id + '"] .chat-area-main');
        activeMessageBody.animate({
            scrollTop: activeMessageBody.prop("scrollHeight")
        }, 100);
    });

    // Function to get the active other user ID
    function get_active_other_user_id() {
        let other_user_id = $('.message-wrapper.is_active').attr('other-user-id');
        return $.trim(other_user_id) || null; 
    }

    // Function to get the active thread ID
    function get_active_thread_id() {
        let chat_id = $('.message-wrapper.is_active').attr('chat-id');
        return chat_id ? chat_id.replace('chat_', '') : null; 
    }
});
