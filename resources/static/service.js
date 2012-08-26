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
            method = 'start';
        }

        if (method && service_name) {
            $.post('/api/service', 'method=' + method + '&name=' + service_name, function(data){
                console.log(data.message);
            }, 'json');
        } else {
            console.log('shit');
        }
    });

    $('a.toggle-enable-service').click(function(){
        var service_name = $(this).attr('rel');
        var enable = !Boolean($(this).children('i.icon-ok').length);
        var target = $(this);
        if (service_name) {
            $.ajax({
                type: 'POST',
                url: '/api/service', 
                data: $.toJSON({method: 'toggle_enable', name: service_name, enable: enable}),
                contentType: 'application/json; charset=UTF-8',
                dataType: 'json'
            }).done(function(data){
                console.log(data.message);
                if (data.status == 0) {
                    if (enable) {
                        target.children('i').removeClass('icon-cancel').addClass('icon-ok');
                    } else {
                        target.children('i').removeClass('icon-ok').addClass('icon-cancel');
                    }
                }
            });
        } else {
            console.log('shit');
        }
    });

    $('a.toggle-autostart-service').click(function(){
        var service_name = $(this).attr('rel');
        var enable = !Boolean($(this).children('i').length);
        var target = $(this);
        if (service_name) {
            $.ajax({
                type: 'POST',
                url: '/api/service', 
                data: $.toJSON({method: 'toggle_autostart', name: service_name, autostart: enable}),
                contentType: 'application/json; charset=UTF-8',
                dataType: 'json'
            }).done(function(data){
                console.log(data.message);
                if (data.status == 0) {
                    if (enable) {
                        target.children('i').removeClass('icon-cancel').addClass('icon-ok');
                    } else {
                        target.children('i').removeClass('icon-ok').addClass('icon-cancel');
                    }
                }
            });
        } else {
            console.log('shit');
        }
    });

    function open_websocket(channel) {
        var WebSocket = window.WebSocket || window.MozWebSocket;

        var socket = new WebSocket('ws://' + location.host + channel);
        console.log('open websocket channel ' + channel + ' done.');

        function reconnect(channel) {
            console.log('do reconnect.');
            return open_websocket(channel);
        }

        socket.onclose = function(event) {
            console.log('lost connection ' + channel);
            self.setTimeout(function(){
                reconnect(channel);
            }, 1000);
        }
	
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

        // socket.onopen = function(event) {
        //     console.log('websocket opened.');
        //     socket.send($.toJSON({method: "start", name: "all"}));
        // }
    }
    open_websocket('/websocket/services_activity');
});
