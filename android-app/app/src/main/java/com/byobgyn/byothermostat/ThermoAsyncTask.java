package com.byobgyn.byothermostat;

import android.os.AsyncTask;
import android.util.Log;

import com.google.gson.Gson;

import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

class ThermoAsyncTask extends AsyncTask<ThermoTaskInput, Void, ThermoReport> {
    private ThermoTaskInput inputTask;
    private static final String TAG = "ThermoAsyncTask";

    @Override
    protected ThermoReport doInBackground(ThermoTaskInput... params) {
        this.inputTask = params[0];

        if(inputTask.isTest()) return null;

        ThermoReport report = null;
        try {
            HttpURLConnection conn = (HttpURLConnection) new URL(inputTask.getUrl()).openConnection();
            conn.setConnectTimeout(500);

            //converting the publickey to base64 format and adding as Basic Authorization.
//                byte[] creds = String.format("%s:", mPublicKey).getBytes();
//                String auth = String.format("Basic %s", Base64.encodeToString(creds, Base64.URL_SAFE));


            Gson gson = new Gson();
//                String payload = gson.toJson(new HLToken(taskInput.getCard()));
//                byte[] bytes = payload.getBytes();

//                conn.setDoOutput(true);
            conn.setDoInput(true);
            conn.setRequestMethod("GET");
//                conn.addRequestProperty("Authorization", auth.trim());
//                conn.addRequestProperty("Content-Type", "application/json");
//                conn.addRequestProperty("Content-Length", String.format("%s", bytes.length));

//                DataOutputStream requestStream = new DataOutputStream(conn.getOutputStream());
//                requestStream.write(bytes);
//                requestStream.flush();
//                requestStream.close();

            try {
                InputStreamReader responseStream = new InputStreamReader(conn.getInputStream());
                report = gson.fromJson(responseStream, ThermoReport.class);
                responseStream.close();
            } catch (IOException e) {
//                int responseCode = conn.getResponseCode();
                Log.d(TAG, "IOException occured " + e.toString());
                throw new IOException(e);
            }

        } catch (Exception e) {
            Log.d(TAG, "Exception occured " + e.toString());
        }

        return report;
    }

    @Override
    protected void onPostExecute(ThermoReport report) {
        ThermoCallback callback = this.inputTask.getCallback();
        if(callback != null)
            callback.onComplete(report);
    }
}
