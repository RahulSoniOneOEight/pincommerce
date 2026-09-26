import fs from "node:fs";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";
import { parse, stringify } from "yaml";

type Doc=Record<string,any>;
type UserAuth={role:"reviewer"|"approver"|"admin";token:string};
const SAFE=/^[A-Za-z0-9._-]+$/;

function resolveAuth(identity:string, suppliedToken:string):UserAuth|null{
  const raw=process.env.REVIEW_MODE_USERS_JSON;
  if(raw){
    try{
      const users=JSON.parse(raw) as Record<string,UserAuth>;
      const user=users[identity];
      if(user && ["reviewer","approver","admin"].includes(user.role) && user.token===suppliedToken) return user;
      return null;
    }catch{return null;}
  }
  const legacy=process.env.REVIEW_MODE_WRITE_TOKEN;
  if(legacy && legacy===suppliedToken) return {role:"reviewer",token:legacy};
  return null;
}

function root(client:string){
  if(!SAFE.test(client)) throw new Error("invalid client");
  return path.resolve(process.cwd(),"../../client-projects",client);
}
function read(file:string):Doc{
  const v=parse(fs.readFileSync(file,"utf8"));
  if(!v||typeof v!=="object") throw new Error("invalid yaml");
  return v as Doc;
}
function findRound(project:string, reviewId:string):{file:string;doc:Doc}{
  const dirs=[path.join(project,"feedback","rounds"),path.join(project,"feedback")];
  const matches:{file:string;doc:Doc}[]=[];
  for(const dir of dirs){
    if(!fs.existsSync(dir)) continue;
    for(const name of fs.readdirSync(dir).filter(x=>x.endsWith(".yaml"))){
      const file=path.join(dir,name);
      try{
        const doc=read(file);
        if(String(doc.review_session_ref||"").endsWith("/"+reviewId+".yaml")||doc.review_id===reviewId) matches.push({file,doc});
      }catch{}
    }
  }
  if(!matches.length) throw new Error("No Review Round bound to this review session");
  return matches.sort((a,b)=>String(a.doc.round_id).localeCompare(String(b.doc.round_id))).at(-1)!;
}
function safeText(v:FormDataEntryValue|null){ return typeof v==="string"?v.trim():""; }

export async function POST(req:NextRequest){
  try{
    const form=await req.formData();
    const client=safeText(form.get("client")), review=safeText(form.get("review"));
    const reviewer=safeText(form.get("reviewer")), requestedRole=safeText(form.get("role")), token=safeText(form.get("token"));
    const surface=safeText(form.get("surface")), journey=safeText(form.get("journey"));
    const comment=safeText(form.get("comment")), action=safeText(form.get("action"));
    if(!client||!review||!reviewer||!surface||!comment) throw new Error("Missing required review fields");
    if(!SAFE.test(review)||!SAFE.test(reviewer)) throw new Error("Invalid review/reviewer identifier");
    const auth=resolveAuth(reviewer,token);
    if(!auth) return NextResponse.json({error:"Review Mode identity or credential denied"},{status:403});
    const role=auth.role;
    if(requestedRole && requestedRole!==role) return NextResponse.json({error:"Requested role does not match configured identity role"},{status:403});
    if(!["approve","request-change"].includes(action)) throw new Error("Unsupported review action");
    if(action==="approve" && !["approver","admin"].includes(role)) return NextResponse.json({error:"Role cannot approve review targets"},{status:403});

    const project=root(client);
    const found=findRound(project,review);
    const round={...found.doc};
    if(!(round.required_surfaces||[]).includes(surface)) throw new Error("Surface is not part of Review Round");
    if(journey&&!(round.required_journeys||[]).includes(journey)) throw new Error("Journey is not part of Review Round");

    const index=(round.feedback_refs||[]).length+1;
    const feedbackId=`FB-${String(round.round_id).replace(/^ROUND-/,"")}-${String(index).padStart(3,"0")}`;
    const classification=action==="approve"?"approval":"minor-change";
    const feedback={
      feedback_id:feedbackId,client_id:client,round_id:round.round_id,
      prototype_revision_ref:round.prototype_revision_ref,surface,journey:journey||null,
      screen:null,component:null,feedback_type:"visual",comment,classification,
      route:action==="approve"?"none":"nowa",action,
      status:action==="approve"?"accepted":"open",evidence_ref:null,
      live_review_ref:null,change_contract_ref:null,created_by:reviewer,
      reviewer_role:role,
      created_at:new Date().toISOString()
    };
    const itemDir=path.join(project,"feedback","items"); fs.mkdirSync(itemDir,{recursive:true});
    const itemFile=path.join(itemDir,feedbackId+".yaml");
    if(fs.existsSync(itemFile)) throw new Error("Feedback id collision");
    fs.writeFileSync(itemFile,stringify(feedback),"utf8");

    round.feedback_refs=[...(round.feedback_refs||[]),`feedback/items/${feedbackId}.yaml`];
    round.outcome=action==="approve"?"in-review":"changes-requested";
    round.surface_decisions=(round.surface_decisions||[]).map((x:Doc)=>x.surface===surface?{...x,status:action==="approve"?"approved":"changes-requested"}:x);
    if(journey) round.journey_decisions=(round.journey_decisions||[]).map((x:Doc)=>x.journey===journey?{...x,status:action==="approve"?"approved":"changes-requested"}:x);
    fs.writeFileSync(found.file,stringify(round),"utf8");

    const back=req.headers.get("referer");
    return NextResponse.redirect(back||new URL("/",req.url),303);
  }catch(error){
    return NextResponse.json({error:error instanceof Error?error.message:"review write failed"},{status:400});
  }
}
