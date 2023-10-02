    document.addEventListener('DOMContentLoaded', function() {
    const likeButton = document.getElementById('likeButton');
    const dislikeButton = document.getElementById('dislikeButton');
    const videoId = document.getElementById('videoContainer').getAttribute('data-id');

    likeButton.addEventListener('click', function() {
        sendReaction(videoId, 1); // 1 for like
    });

    dislikeButton.addEventListener('click', function() {
        sendReaction(videoId, 0); // 0 for dislike
    });

    function sendReaction(videoId, isLike) {
        var xhr = new XMLHttpRequest();
        var method = 'POST';
        var url = '/react/video';

        xhr.open(method, url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');

        xhr.onload = function() {
            if (xhr.status === 200) {
                console.log('Reaction sent successfully');
            } else {
                console.error('An error occurred while sending the reaction.');
            }
        };

        xhr.onerror = function() {
            console.error('An error occurred while executing the request.');
        };

        xhr.send(JSON.stringify({ VideoId: videoId, IsLike: isLike }));
        location.reload()
    }
});
document.addEventListener('DOMContentLoaded', function() {
    const commentButton = document.getElementById('commentButton');
    const commentText = document.getElementById('commentText');
    const commentList = document.querySelector('.comment-list');
    const videoId = document.getElementById('videoContainer').getAttribute('data-id');

    commentButton.addEventListener('click', function() {
        const text = commentText.value;
        if (text.trim() === '') {
            alert('Please enter a comment.');
            return;
        }
        
        sendComment(videoId, text);
    });

    function sendComment(videoId, text) {
        var xhr = new XMLHttpRequest();
        var method = 'POST';
        var url = '/comment/video';

        xhr.open(method, url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');

        xhr.onload = function() {
            if (xhr.status === 200) {
                console.log('Comment sent successfully');
                // Assuming the response contains the new comment data
                const newComment = JSON.parse(xhr.responseText);
                appendComment(newComment);
            } else {
                console.error('An error occurred while sending the comment.');
            }
        };

        xhr.onerror = function() {
            console.error('An error occurred while executing the request.');
        };

        xhr.send(JSON.stringify({ VideoId: videoId, Text: text }));
        location.reload()
    }
    
});

