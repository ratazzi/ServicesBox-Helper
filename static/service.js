$(document).ready(function(){
    $("#start-all-services,#stop-all-services,#restart-all-services").click(function(){
        var text = $(this).attr('id');

        var method = null;
        if (text.match('restart')) {
            console.log('restart all service');
            method = 'restart';
        } else if (text.match('stop')) {
            console.log('stop all service');
            method = 'stop';
        } else if (text.match('start')) {
            console.log('start all service');
            method = 'start';
        }

        if (method) {
            $.post('/api/service', 'method=' + method + '&name=all', function(data){
                console.log(data.message);
            }, 'json');
        } else {
            console.log('shit');
        }
    });

    $("button.start-service,button.stop-service,button.restart-service").click(function(){
        var text = $(this).attr('class');
        var service_name = $(this).attr("name");

        if (text.match('active')) {
            console.log('skiped.');
            return false;
        }

        var method = null;
        if (text.match('restart')) {
            console.log('restart service ' + service_name);
            method = 'restart';
        } else if (text.match('stop')) {
            console.log('stop service ' + service_name);
            method = 'stop';
        } else if (text.match('start')) {
            console.log('start service ' + service_name);
            method = 'restart';
        }

        if (method && service_name) {
            $.post('/api/service', 'method=' + method + '&name=' + service_name, function(data){
                console.log(data.message);
            }, 'json');
        } else {
            console.log('shit');
        }
    });

    var WebSocket = window.WebSocket || window.MozWebSocket;

    if (WebSocket) {
        try {
            var socket = new WebSocket('ws://' + location.host + '/websocket/services_activity');
        } catch(e) {
            console.log('open websocket failed.');
        }
    }

    if (socket) {
        socket.onmessage = function(event) {
            var data = $.parseJSON(event.data);
            // console.log(data);
            $.each(data, function(){
                // console.log(this);
                var service = $('#' + this.name);
                // service.find('i.status').removeClass('');
                // console.log(service.find('h4').text());
                if (this.running) {
                    service.find('i.icon-stop').removeClass('icon-stop').addClass('icon-play');
                    service.find('button.start-service').addClass('active');
                    service.find('button.stop-service').removeClass('active');
                } else {
                    service.find('button.start-service').removeClass('active');
                    service.find('button.stop-service').addClass('active');
                    service.find('i.icon-play').removeClass('icon-play').addClass('icon-stop');
                }
            });
        }

        socket.onopen = function(event) {
            console.log('websocket opened.');
            socket.send($.toJSON({method: "start", name: "all"}));
        }

        socket.onclose = function(event) {
            console.log('websocket closed. ');
            if (!socket) {
                self.setInterval(function(){
                    try {
                        console.log('reconnect ...');
                        socket = new WebSocket('ws://' + location.host + '/websocket/services_activity');
                    } catch (e) {
                        console.log('reconnect failed.');
                    }
                }, 300);
            }
        }
    }
});
