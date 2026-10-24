package com.sentient.build;

import com.android.apksig.ApkSigner;
import java.io.File;
import java.io.FileInputStream;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.cert.X509Certificate;
import java.util.Collections;
import java.util.List;

public class ApkSignerCli {
    public static void main(String[] args) throws Exception {
        if (args.length < 5) {
            System.err.println("Usage: ApkSignerCli <inputApk> <outputApk> <keystorePath> <alias> <password>");
            System.exit(1);
        }

        File inputApk = new File(args[0]);
        File outputApk = new File(args[1]);
        File keystoreFile = new File(args[2]);
        String alias = args[3];
        char[] password = args[4].toCharArray();

        KeyStore ks = KeyStore.getInstance(KeyStore.getDefaultType());
        try (FileInputStream fis = new FileInputStream(keystoreFile)) {
            ks.load(fis, password);
        }

        PrivateKey privateKey = (PrivateKey) ks.getKey(alias, password);
        X509Certificate cert = (X509Certificate) ks.getCertificate(alias);
        List<X509Certificate> certs = Collections.singletonList(cert);

        ApkSigner.SignerConfig signerConfig =
            new ApkSigner.SignerConfig.Builder(alias, privateKey, certs).build();

        ApkSigner apkSigner = new ApkSigner.Builder(Collections.singletonList(signerConfig))
            .setInputApk(inputApk)
            .setOutputApk(outputApk)
            .setV1SigningEnabled(true)
            .setV2SigningEnabled(true)
            .setV3SigningEnabled(true)
            .build();

        apkSigner.sign();
        System.out.println("[SUCCESS] APK successfully signed with V1 + V2 + V3 schemes!");
    }
}
