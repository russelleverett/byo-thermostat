package com.byobgyn.byothermostat;

class ThermoTaskInput {
    private String url;
    private String data;
    private ThermoCallback callback;
    private boolean test = false;

    public String getUrl() {
        return url;
    }
    public String getData() {
        return data;
    }
    public ThermoCallback getCallback() {
        return callback;
    }
    public boolean isTest() {
        return test;
    }

    public ThermoTaskInput(String url, ThermoCallback callback) {
        this(url, null, callback, false);
    }
    public ThermoTaskInput(String url, ThermoCallback callback, boolean isTest) {
        this(url, null, callback, isTest);
    }
    public ThermoTaskInput(String url, String data, ThermoCallback callback, boolean isTest) {
        this.url = url;
        this.data = data;
        this.callback = callback;
        this.test = isTest;
    }
}
