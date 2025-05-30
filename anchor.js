const fs = require("fs");
const axios = require("axios");
const crypto = require("crypto");
const nanocurrency = require("nanocurrency");

// === CONFIG ===
const seed = "NANO_WALLET_PRIVATE_KEY";
const index = 0;
const rpcURL = "https://rpc.nano.to";
const rpcAuth = "Bearer RPC_API_KEY";

// === Load anchor
const anchor = JSON.parse(fs.readFileSync("../daily_log_anchor.json", "utf8"));
const snapshotHash = anchor.snapshot_hash;
const timestamp = anchor.timestamp;

// === Derive account + keys
const privateKey = nanocurrency.deriveSecretKey(seed, index);
const publicKey = nanocurrency.derivePublicKey(privateKey);
const address = nanocurrency.deriveAddress(publicKey, { useNanoPrefix: true });

console.log("🔐 Address:", address);
console.log("🔑 Public Key:", publicKey.toLowerCase());
console.log("📄 Snapshot Hash (raw):", snapshotHash);

async function rpc(action, params = {}) {
    const res = await axios.post(rpcURL, {
        action,
        ...params,
    }, {
        headers: {
            Authorization: rpcAuth,
            "Content-Type": "application/json",
        },
    });
    return res.data;
}

(async () => {
    try {
        const info = await rpc("account_info", { account: address });
        console.log("📦 Account Info:", info);
        const frontier = info.frontier;
        const balance = BigInt(info.balance);
        console.log("📊 Balance:", balance);
        const newBalance = balance - 1n;
        console.log("📊 New Balance:", newBalance);

        const workRes = await rpc("work_generate", { hash: frontier });
        const work = workRes.work;

        const { parseAddress } = require('nanocurrency'); // USE `npm i nanocurrency`

        let linkHex;
        if (snapshotHash.startsWith("nano_")) {
            linkHex = parseAddress(snapshotHash).publicKey; // public key hex of address
        } else if (/^[0-9a-f]{64}$/.test(snapshotHash)) {
            linkHex = snapshotHash.toLowerCase();           // direct hex string
        } else {
            linkHex = crypto.createHash("sha256").update(snapshotHash).digest("hex"); // hashed string
        }


        // === Build block
        const block = {
            type: "state",
            account: address,             
            previous: frontier,
            representative: address,      
            balance: newBalance.toString(),
            link: linkHex,
            work: work,
        };

        console.log("🔍 Block for hashing:");
        console.dir(block, { depth: null });

        const blockHash = await nanocurrency.hashBlock(block);
        console.log("🔗 Block Hash:", blockHash);
        const blockHashBytes = Buffer.from(blockHash, "hex");
        console.log("🔗 blockHashBytes:", blockHashBytes);
        const signature = nanocurrency.signBlock({
            hash: blockHash,
            secretKey: privateKey
        });
        block.signature = signature;

        console.log("📦 Final Block for Submission:");
        console.dir(block, { depth: null });

        const result = await rpc("process", {
            json_block: true,
            subtype: "send",
            block: block,
        });

        if (result.hash) {
            console.log("✅ Anchored successfully!");
            console.log("🔗 TX Hash:", result.hash);

            fs.writeFileSync("nano_tx_proof.json", JSON.stringify({
                snapshot_hash: snapshotHash,
                nano_tx_hash: result.hash,
                nano_address: address,
                timestamp
            }, null, 2));
        } else {
            console.error("❌ Failed to anchor:", result);
        }
    } catch (err) {
        console.error("❌ Error:", err.response?.data || err.message);
    }
})();
