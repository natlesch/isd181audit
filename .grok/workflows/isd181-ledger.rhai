let meta = #{
    name: "isd181-ledger",
    description: "Challenge the ISD 181 ledger plan, then build and review the tracker",
    phases: [
        #{ title: "Challenge", detail: "two read-only skeptics" },
        #{ title: "Build", detail: "one implementer if no blocker survived" },
        #{ title: "Review", detail: "run the tests and try to show a mixed total" },
    ],
};

let challenge_schema = #{
    "type": "object",
    "required": ["blockers", "required_changes"],
    "properties": #{
        "blockers": #{ "type": "array", "maxItems": 6, "items": #{ "type": "string" } },
        "required_changes": #{ "type": "array", "maxItems": 6, "items": #{ "type": "string" } },
    },
};

let build_schema = #{
    "type": "object",
    "required": ["tests_passed", "files"],
    "properties": #{
        "tests_passed": #{ "type": "boolean" },
        "files": #{ "type": "array", "items": #{ "type": "string" } },
        "notes": #{ "type": "string" },
    },
};

let review_schema = #{
    "type": "object",
    "required": ["approved", "tests_passed", "defects"],
    "properties": #{
        "approved": #{ "type": "boolean" },
        "tests_passed": #{ "type": "boolean" },
        "defects": #{ "type": "array", "maxItems": 8, "items": #{ "type": "string" } },
        "evidence": #{ "type": "string" },
    },
};

phase("Challenge");

let numbers_prompt = "You are a skeptical reviewer of dollar amounts. Do not edit anything. Repo: /home/mint/projects/isd181. Read docs/PLAN.md, data/lines.csv, and sources/text/fy2025-audit.txt and sources/text/fy2026-statutory.txt. Use grep and read_file. A blocker is only a locked dollar amount in the plan or lines.csv that contradicts those text extracts. Quote the line id or the plan sentence and the source line. Rounding of one to three dollars that the plan already names is not a blocker. Put wording tightenings in required_changes. If you find no contradiction, blockers is empty.";

let basis_prompt = "You are a skeptical reviewer of accounting bases. Do not edit anything. Repo: /home/mint/projects/isd181. Read docs/PLAN.md and the header plus a sample of data/lines.csv. Use grep and read_file. A blocker is only one of these: a rule that puts internal service, the custodial fund, government-wide expenses, or statutory inflows into the governmental-fund headline; a rule that treats FY2026 statutory general-fund inflows as FY2025 audited general-fund revenue; a rule that sets the FY2027 beginning balance equal to the FY2026 statutory ending balance. An unexplained gap between budget vintages is not a blocker. Quote the plan sentence. If none of those rules are present, blockers is empty and any extra caution goes in required_changes.";

let challenges = parallel([
    #{
        prompt: numbers_prompt,
        label: "challenge:numbers",
        capability_mode: "read-only",
        agent_type: "explore",
        output_schema: challenge_schema,
    },
    #{
        prompt: basis_prompt,
        label: "challenge:basis",
        capability_mode: "read-only",
        agent_type: "explore",
        output_schema: challenge_schema,
    },
]);

let blocked = false;
let amendments = "";
for r in challenges {
    if r == () || r.success != true || r.output == () || type_of(r.output) != "map" {
        blocked = true;
        amendments += "BLOCKER: skeptic returned nothing usable\n";
    } else {
        let blockers = r.output.blockers;
        if type_of(blockers) == "array" {
            for b in blockers {
                if type_of(b) == "string" && b != "" {
                    blocked = true;
                    amendments += "BLOCKER: " + b + "\n";
                }
            }
        }
        let changes = r.output.required_changes;
        if type_of(changes) == "array" {
            for c in changes {
                if type_of(c) == "string" && c != "" {
                    amendments += "CHANGE: " + c + "\n";
                }
            }
        }
    }
}

if blocked {
    complete(#{
        status: "blocked",
        amendments: amendments,
    });
}

phase("Build");

let spec = "Implement the Brainerd ISD 181 tracker. Read /home/mint/projects/isd181/docs/PLAN.md and follow the Build contract section. Do not modify data/, sources/, or docs/. Do not run bd. Do not git commit or push. Do not add dependencies. Python 3 standard library only.\n";
spec += "Run: cd /home/mint/projects/isd181 && PYTHONPATH=src python3 -m unittest discover -s tests -v && PYTHONPATH=src python3 -m isd181\n";
spec += "tests_passed is true only if that command exits 0. files lists the paths you created.\n";
spec += "Skeptic notes follow. Apply a CHANGE when it does not contradict the plan and does not change a published number. Ignore empty text.\n";
spec += amendments;

let built = agent(spec, #{
    label: "build:ledger",
    capability_mode: "execute",
    agent_type: "general-purpose",
    output_schema: build_schema,
});

phase("Review");

let review_prompt = "Adversarially review the ISD 181 tracker at /home/mint/projects/isd181. Do not commit, push, or run bd. Do not edit files except if you must, and you must not: this is a review, so do not edit. Read docs/PLAN.md. Run cd /home/mint/projects/isd181 && PYTHONPATH=src python3 -m unittest discover -s tests -v && PYTHONPATH=src python3 -m isd181. Read output/income-spending.md. approved is true only if the tests pass AND you cannot show that the governmental-fund headline includes internal service, custodial funds, government-wide expenses, or statutory inflows. defects lists only problems you verified. evidence quotes the unittest result line and one headline sentence from the report.\n";
review_prompt += "Builder output and amendments:\n";
review_prompt += amendments;

let reviewed = agent(review_prompt, #{
    label: "review:ledger",
    capability_mode: "execute",
    agent_type: "general-purpose",
    output_schema: review_schema,
});

let approved = false;
let tests_passed = false;
let defects = "";
if reviewed != () && reviewed.success == true && type_of(reviewed.output) == "map" {
    approved = reviewed.output.approved == true;
    tests_passed = reviewed.output.tests_passed == true;
    if type_of(reviewed.output.defects) == "array" {
        for d in reviewed.output.defects {
            if type_of(d) == "string" && d != "" {
                defects += d + "\n";
            }
        }
    }
}

let status = "failed";
if approved && tests_passed && defects == "" {
    status = "approved";
}

complete(#{
    status: status,
    amendments: amendments,
    defects: defects,
});
