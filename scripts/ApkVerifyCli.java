package com.sentient.build;

import com.android.apksig.ApkVerifier;
import java.io.File;

public class ApkVerifyCli {
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("Usage: ApkVerifyCli <apkPath>");
            System.exit(1);
        }

        File apkFile = new File(args[0]);
        ApkVerifier verifier = new ApkVerifier.Builder(apkFile).build();
        ApkVerifier.Result result = verifier.verify();

        System.out.println("Verification Result:");
        System.out.println("  isVerified:   " + result.isVerified());
        System.out.println("  verifiedUsingV1Scheme: " + result.isVerifiedUsingV1Scheme());
        System.out.println("  verifiedUsingV2Scheme: " + result.isVerifiedUsingV2Scheme());
        System.out.println("  verifiedUsingV3Scheme: " + result.isVerifiedUsingV3Scheme());

        if (!result.isVerified()) {
            System.err.println("Errors found:");
            for (ApkVerifier.IssueWithParams issue : result.getErrors()) {
                System.err.println("  ERROR: " + issue);
            }
            System.exit(2);
        }
    }
}
